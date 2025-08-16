# Configuration Scénarios

## Vue d'ensemble

La page de configuration des scénarios permet de créer, gérer et comparer différents scénarios de projet photovoltaïque: variantes techniques, financières, et économiques pour optimiser la prise de décision et analyser les risques et opportunités.

## Structure de la page

### Header de Configuration
```typescript
interface ScenariosHeader {
 title: " Scénarios";

 overview: {
 totalScenarios: number;
 activeScenarios: number;

 baseline: {
 name: string;
 status: "configured" | "calculating" | "completed";

 keyMetrics: {
 van: number;
 tri: number;
 payback: number;
 };
 };

 comparison: {
 bestVan: {
 scenario: string;
 value: number;
 improvement: number;
 };

 bestTri: {
 scenario: string;
 value: number;
 improvement: number;
 };

 lowestRisk: {
 scenario: string;
 risk: number;
 advantage: number;
 };
 };
 };

 actions: {
 create: {
 label: "Nouveau scénario";
 icon: "add_circle";

 methods: [
 {
 id: "blank";
 label: "Vierge";
 description: "Créer un nouveau scénario";
 },
 {
 id: "duplicate";
 label: "Dupliquer";
 description: "Copier un scénario existant";
 },
 {
 id: "template";
 label: "Depuis template";
 description: "Utiliser un modèle prédéfini";
 },
 {
 id: "wizard";
 label: "Assistant";
 description: "Création guidée par étapes";
 }
 ];

 onClick: (method: string) => void;
 };

 compare: {
 label: "Comparer scénarios";
 icon: "compare_arrows";

 selection: {
 scenarios: string[];

 criteria: [
 "Indicateurs financiers",
 "Risques",
 "Paramètres techniques",
 "Structure de financement"
 ];
 };

 onClick: () => void;
 };

 optimize: {
 label: "Optimiser";
 icon: "tune";

 methods: [
 "Maximiser VAN",
 "Minimiser risques",
 "Équilibrer rendement/risque"
 ];

 onClick: (method: string) => void;
 };

 export: {
 label: "Exporter";
 icon: "download";

 formats: [
 { id: "xlsx", label: "Excel", description: "Tableaux détaillés" },
 { id: "pdf", label: "PDF", description: "Rapport complet" },
 { id: "pptx", label: "PowerPoint", description: "Présentation" }
 ];

 onClick: (format: string) => void;
 };
 };
}
```

### Section Gestion des Scénarios
```typescript
interface ScenarioManagementSection {
 title: " Gestion des scénarios";

 scenarioList: {
 view: "table" | "cards" | "comparison";

 table: {
 columns: [
 {
 id: "name";
 label: "Nom";
 sortable: true;

 cell: {
 editable: boolean;

 validation: {
 required: boolean;
 unique: boolean;
 maxLength: number;
 };
 };
 },
 {
 id: "type";
 label: "Type";
 sortable: true;

 cell: {
 type: "badge";

 options: [
 { value: "baseline", label: "Référence", color: "blue" },
 { value: "optimistic", label: "Optimiste", color: "green" },
 { value: "pessimistic", label: "Pessimiste", color: "red" },
 { value: "alternative", label: "Alternative", color: "purple" },
 { value: "sensitivity", label: "Sensibilité", color: "orange" }
 ];
 };
 },
 {
 id: "status";
 label: "Statut";
 sortable: true;

 cell: {
 type: "status";

 options: [
 { value: "draft", label: "Brouillon", color: "gray", icon: "edit" },
 { value: "configured", label: "Configuré", color: "blue", icon: "settings" },
 { value: "calculating", label: "Calcul en cours", color: "yellow", icon: "sync" },
 { value: "completed", label: "Terminé", color: "green", icon: "check_circle" },
 { value: "error", label: "Erreur", color: "red", icon: "error" }
 ];
 };
 },
 {
 id: "van";
 label: "VAN";
 sortable: true;
 unit: "€";

 cell: {
 type: "number";

 formatting: {
 currency: true;
 precision: 0;
 };

 comparison: {
 baseline: boolean;

 indicator: {
 type: "arrow" | "percentage";

 color: "green" | "red" | "neutral";
 };
 };
 };
 },
 {
 id: "tri";
 label: "TRI";
 sortable: true;
 unit: "%";

 cell: {
 type: "percentage";

 formatting: {
 precision: 1;
 };

 thresholds: {
 excellent: 12;
 good: 8;
 acceptable: 5;
 };
 };
 },
 {
 id: "payback";
 label: "Payback";
 sortable: true;
 unit: "ans";

 cell: {
 type: "number";

 formatting: {
 precision: 1;
 };

 target: {
 max: 10;

 color: "green" | "orange" | "red";
 };
 };
 },
 {
 id: "risk";
 label: "Risque";
 sortable: true;

 cell: {
 type: "risk-indicator";

 level: "low" | "medium" | "high";

 breakdown: {
 technical: number;
 financial: number;
 regulatory: number;
 market: number;
 };
 };
 },
 {
 id: "lastModified";
 label: "Modifié";
 sortable: true;

 cell: {
 type: "date";

 format: "relative";

 author: string;
 };
 },
 {
 id: "actions";
 label: "Actions";

 buttons: [
 {
 id: "edit";
 label: "Modifier";
 icon: "edit";

 onClick: (scenario: Scenario) => void;
 },
 {
 id: "duplicate";
 label: "Dupliquer";
 icon: "content_copy";

 onClick: (scenario: Scenario) => void;
 },
 {
 id: "calculate";
 label: "Calculer";
 icon: "calculate";

 onClick: (scenario: Scenario) => void;

 disabled: boolean;
 },
 {
 id: "delete";
 label: "Supprimer";
 icon: "delete";

 onClick: (scenario: Scenario) => void;

 confirm: {
 title: string;
 message: string;
 };
 }
 ];
 }
 ];

 data: Scenario[];

 selection: {
 enabled: boolean;

 selected: string[];

 actions: [
 {
 id: "bulk_calculate";
 label: "Calculer sélection";
 icon: "calculate";

 onClick: (scenarios: string[]) => void;
 },
 {
 id: "bulk_compare";
 label: "Comparer";
 icon: "compare";

 onClick: (scenarios: string[]) => void;
 },
 {
 id: "bulk_export";
 label: "Exporter";
 icon: "download";

 onClick: (scenarios: string[]) => void;
 }
 ];
 };

 filtering: {
 type: string[];
 status: string[];

 range: {
 van: [number, number];
 tri: [number, number];
 risk: [number, number];
 };

 search: {
 query: string;

 fields: ["name", "description", "tags"];
 };
 };

 sorting: {
 field: string;
 direction: "asc" | "desc";

 secondary: {
 field: string;
 direction: "asc" | "desc";
 };
 };
 };

 cards: {
 layout: "grid" | "masonry";

 card: {
 header: {
 name: string;
 type: ScenarioType;
 status: ScenarioStatus;

 actions: CardAction[];
 };

 content: {
 description: string;

 metrics: {
 primary: {
 van: number;
 tri: number;
 payback: number;
 };

 secondary: {
 investment: number;
 revenue: number;
 risk: number;
 };
 };

 progress: {
 configuration: number;
 calculation: number;

 nextSteps: string[];
 };

 variations: {
 [parameter: string]: {
 baseline: any;
 current: any;

 impact: "positive" | "negative" | "neutral";
 };
 };
 };

 footer: {
 lastModified: Date;
 author: string;

 tags: string[];

 quickActions: QuickAction[];
 };
 };
 };
 };

 bulkActions: {
 label: "Actions groupées";

 selection: {
 all: boolean;
 scenarios: string[];

 actions: [
 {
 id: "calculate_all";
 label: "Calculer tous";
 icon: "calculate";

 batch: {
 size: number;

 parallel: boolean;

 progress: {
 current: number;
 total: number;

 eta: number;
 };
 };

 onClick: (scenarios: string[]) => void;
 },
 {
 id: "update_parameters";
 label: "Mettre à jour paramètres";
 icon: "sync";

 fields: [
 "technology",
 "financing",
 "tariffs",
 "costs"
 ];

 onClick: (scenarios: string[], updates: any) => void;
 },
 {
 id: "generate_report";
 label: "Générer rapport";
 icon: "description";

 templates: ReportTemplate[];

 onClick: (scenarios: string[], template: string) => void;
 }
 ];
 };
 };
}
```

### Section Configuration Scénario
```typescript
interface ScenarioConfigurationSection {
 title: " Configuration scénario";

 selection: {
 current: string;

 selector: {
 type: "dropdown" | "tabs";

 scenarios: Scenario[];

 search: {
 enabled: boolean;

 placeholder: "Rechercher un scénario...";
 };

 grouping: {
 enabled: boolean;

 by: "type" | "status" | "author";
 };
 };

 navigation: {
 previous: () => void;
 next: () => void;

 shortcuts: {
 enabled: boolean;

 keys: KeyboardShortcut[];
 };
 };
 };

 metadata: {
 basic: {
 name: {
 label: "Nom du scénario";
 type: "text";
 value: string;

 validation: {
 required: boolean;
 unique: boolean;
 maxLength: number;
 };
 };

 description: {
 label: "Description";
 type: "textarea";
 value: string;

 maxLength: number;

 placeholder: "Décrivez les spécificités de ce scénario...";
 };

 type: {
 label: "Type de scénario";
 type: "select";
 value: string;

 options: [
 {
 value: "baseline";
 label: "Référence";
 description: "Scénario de base pour comparaisons";

 characteristics: [
 "Hypothèses moyennes",
 "Risques standards",
 "Pas d'optimisation"
 ];
 },
 {
 value: "optimistic";
 label: "Optimiste";
 description: "Hypothèses favorables";

 characteristics: [
 "Production élevée",
 "Coûts réduits",
 "Conditions favorables"
 ];
 },
 {
 value: "pessimistic";
 label: "Pessimiste";
 description: "Hypothèses défavorables";

 characteristics: [
 "Production réduite",
 "Coûts élevés",
 "Conditions difficiles"
 ];
 },
 {
 value: "alternative";
 label: "Alternative";
 description: "Variante technique ou financière";

 characteristics: [
 "Technologie différente",
 "Financement alternatif",
 "Stratégie modifiée"
 ];
 },
 {
 value: "sensitivity";
 label: "Sensibilité";
 description: "Test de sensibilité paramétrique";

 characteristics: [
 "Variation paramètre",
 "Analyse d'impact",
 "Évaluation robustesse"
 ];
 }
 ];
 };

 tags: {
 label: "Tags";
 type: "tags";
 value: string[];

 suggestions: [
 "Technique",
 "Financier",
 "Réglementaire",
 "Marché",
 "Risque",
 "Opportunité"
 ];

 custom: {
 allowed: boolean;

 validation: {
 maxLength: number;

 format: RegExp;
 };
 };
 };

 author: {
 label: "Auteur";
 type: "user";
 value: string;

 readOnly: boolean;

 collaboration: {
 contributors: string[];

 permissions: {
 [userId: string]: "read" | "write" | "admin";
 };
 };
 };
 };

 reference: {
 baseline: {
 label: "Scénario de référence";
 type: "select";
 value: string;

 options: Scenario[];

 comparison: {
 enabled: boolean;

 metrics: string[];

 visualization: {
 type: "side_by_side" | "overlay" | "difference";
 };
 };
 };

 derivedFrom: {
 label: "Dérivé de";
 type: "select";
 value: string;

 options: Scenario[];

 inheritance: {
 parameters: string[];

 overrides: Override[];
 };
 };
 };

 versioning: {
 version: {
 label: "Version";
 type: "text";
 value: string;

 automatic: {
 enabled: boolean;

 scheme: "major.minor.patch" | "sequential" | "timestamp";
 };
 };

 history: {
 label: "Historique";

 versions: [
 {
 version: string;
 date: Date;
 author: string;

 changes: [
 {
 field: string;
 before: any;
 after: any;

 impact: "minor" | "major" | "critical";
 }
 ];

 actions: {
 restore: () => void;
 compare: () => void;

 export: () => void;
 };
 }
 ];
 };
 };
 };

 parameters: {
 sections: [
 {
 id: "technical";
 label: "Paramètres techniques";
 icon: "settings";

 inheritanceMode: "inherit" | "override" | "custom";

 fields: {
 technology: {
 label: "Technologie";

 inheritance: {
 from: "baseline";

 override: {
 enabled: boolean;

 value: string;

 reason: string;
 };
 };

 value: string;

 options: Technology[];

 impact: {
 onProduction: number;
 onCost: number;
 onRisk: number;
 };
 };

 power: {
 label: "Puissance";

 inheritance: {
 from: "baseline";

 override: {
 enabled: boolean;

 value: number;

 reason: string;
 };
 };

 value: number;
 unit: "kWc";

 variation: {
 type: "absolute" | "relative";

 absolute: {
 value: number;

 impact: {
 investment: number;
 revenue: number;
 };
 };

 relative: {
 percentage: number;

 reference: "baseline";

 impact: {
 investment: number;
 revenue: number;
 };
 };
 };
 };

 production: {
 label: "Production";

 calculation: {
 method: "automatic" | "manual" | "adjustment";

 automatic: {
 dependencies: [
 "power",
 "technology",
 "location",
 "orientation"
 ];

 recalculate: {
 onParameterChange: boolean;

 trigger: string[];
 };
 };

 manual: {
 value: number;
 unit: "MWh/an";

 justification: string;
 };

 adjustment: {
 baseline: number;

 factor: number;

 reason: string;
 };
 };

 uncertainty: {
 enabled: boolean;

 range: {
 min: number;
 max: number;

 distribution: "normal" | "uniform" | "triangular";
 };

 scenarios: {
 p10: number;
 p50: number;
 p90: number;
 };
 };
 };

 performance: {
 label: "Performance";

 pr: {
 label: "Performance Ratio";
 type: "number";
 value: number;
 unit: "%";

 factors: {
 temperature: number;
 soiling: number;
 shading: number;
 mismatch: number;

 inverter: number;
 cables: number;
 availability: number;
 };
 };

 degradation: {
 label: "Dégradation";
 type: "number";
 value: number;
 unit: "%/an";

 profile: {
 type: "linear" | "exponential" | "custom";

 custom: {
 years: number[];
 rates: number[];
 };
 };
 };
 };
 };
 },

 {
 id: "economic";
 label: "Paramètres économiques";
 icon: "attach_money";

 inheritanceMode: "inherit" | "override" | "custom";

 fields: {
 investment: {
 label: "Investissement";

 structure: {
 method: "total" | "detailed";

 total: {
 amount: number;
 unit: "€";

 variation: {
 type: "absolute" | "relative";

 value: number;

 reference: "baseline";
 };
 };

 detailed: {
 categories: [
 {
 id: "equipment";
 label: "Équipements";
 amount: number;

 variation: {
 enabled: boolean;

 type: "absolute" | "relative";

 value: number;

 justification: string;
 };
 },
 {
 id: "installation";
 label: "Installation";
 amount: number;

 variation: {
 enabled: boolean;

 type: "absolute" | "relative";

 value: number;

 justification: string;
 };
 },
 {
 id: "development";
 label: "Développement";
 amount: number;

 variation: {
 enabled: boolean;

 type: "absolute" | "relative";

 value: number;

 justification: string;
 };
 }
 ];

 total: number;
 };
 };

 financing: {
 structure: FinancingStructure;

 variations: {
 equity: {
 enabled: boolean;

 percentage: number;

 impact: {
 onCost: number;
 onRisk: number;
 };
 };

 debt: {
 enabled: boolean;

 rate: number;
 duration: number;

 impact: {
 onCost: number;
 onCashflow: number;
 };
 };
 };
 };
 };

 revenue: {
 label: "Revenus";

 structure: {
 contractType: string;

 variations: {
 tariff: {
 enabled: boolean;

 rate: number;

 evolution: {
 type: "fixed" | "indexed" | "custom";

 indexed: {
 index: "inflation" | "energy" | "custom";

 rate: number;
 };

 custom: {
 years: number[];
 rates: number[];
 };
 };
 };

 autoconsommation: {
 enabled: boolean;

 rate: number;

 electricityPrice: {
 current: number;

 evolution: {
 type: "scenario";

 scenario: "conservative" | "moderate" | "aggressive";

 rates: number[];
 };
 };
 };
 };
 };

 subsidies: {
 enabled: boolean;

 items: [
 {
 id: string;
 name: string;
 amount: number;

 variation: {
 enabled: boolean;

 probability: number;

 adjustedAmount: number;
 };
 }
 ];
 };
 };

 costs: {
 label: "Coûts d'exploitation";

 structure: {
 method: "simplified" | "detailed";

 simplified: {
 annual: number;
 unit: "€/an";

 evolution: {
 type: "fixed" | "indexed";

 indexed: {
 rate: number;

 base: "inflation" | "capacity" | "custom";
 };
 };
 };

 detailed: {
 categories: [
 {
 id: "maintenance";
 label: "Maintenance";
 amount: number;

 structure: {
 preventive: number;
 corrective: number;

 provisioning: number;
 };
 },
 {
 id: "insurance";
 label: "Assurance";
 amount: number;

 calculation: {
 rate: number;

 base: "investment" | "revenue";
 };
 },
 {
 id: "administration";
 label: "Administration";
 amount: number;

 breakdown: {
 accounting: number;
 legal: number;
 reporting: number;
 };
 }
 ];
 };
 };
 };
 };
 },

 {
 id: "financial";
 label: "Paramètres financiers";
 icon: "account_balance";

 inheritanceMode: "inherit" | "override" | "custom";

 fields: {
 analysis: {
 label: "Analyse financière";

 duration: {
 label: "Durée d'analyse";
 type: "number";
 value: number;
 unit: "ans";

 variation: {
 enabled: boolean;

 value: number;

 impact: {
 onVan: number;
 onTri: number;
 };
 };
 };

 discountRate: {
 label: "Taux d'actualisation";
 type: "number";
 value: number;
 unit: "%";

 variation: {
 enabled: boolean;

 value: number;

 justification: string;

 impact: {
 onVan: number;

 sensitivity: number;
 };
 };
 };

 inflation: {
 label: "Inflation";
 type: "number";
 value: number;
 unit: "%";

 application: {
 costs: boolean;
 revenues: boolean;

 selective: {
 enabled: boolean;

 rates: {
 [category: string]: number;
 };
 };
 };
 };
 };

 taxation: {
 label: "Fiscalité";

 regime: {
 type: "select";
 value: string;

 options: [
 {
 value: "is";
 label: "Impôt sur les sociétés";
 rate: 25;
 },
 {
 value: "ir";
 label: "Impôt sur le revenu";

 marginalRate: number;
 },
 {
 value: "exonerated";
 label: "Exonéré";

 conditions: string[];
 }
 ];
 };

 depreciation: {
 method: "linear" | "declining" | "accelerated";

 duration: number;

 rate: number;

 benefits: {
 immediate: number;
 deferred: number;

 total: number;
 };
 };
 };
 };
 },

 {
 id: "risks";
 label: "Risques";
 icon: "warning";

 inheritanceMode: "inherit" | "override" | "custom";

 assessment: {
 method: "qualitative" | "quantitative" | "mixed";

 qualitative: {
 categories: [
 {
 id: "technical";
 label: "Technique";

 risks: [
 {
 id: "technology";
 label: "Risque technologique";
 level: "low" | "medium" | "high";

 impact: number;
 probability: number;

 mitigation: string[];
 },
 {
 id: "performance";
 label: "Risque de performance";
 level: "low" | "medium" | "high";

 impact: number;
 probability: number;

 mitigation: string[];
 }
 ];
 },
 {
 id: "financial";
 label: "Financier";

 risks: [
 {
 id: "interest_rate";
 label: "Risque de taux";
 level: "low" | "medium" | "high";

 impact: number;
 probability: number;

 mitigation: string[];
 },
 {
 id: "inflation";
 label: "Risque inflation";
 level: "low" | "medium" | "high";

 impact: number;
 probability: number;

 mitigation: string[];
 }
 ];
 }
 ];
 };

 quantitative: {
 method: "monte_carlo" | "sensitivity" | "scenario";

 monte_carlo: {
 iterations: number;

 variables: [
 {
 name: string;
 distribution: "normal" | "uniform" | "triangular";

 parameters: number[];
 };
 ];

 results: {
 van: {
 mean: number;
 std: number;

 percentiles: {
 p10: number;
 p50: number;
 p90: number;
 };
 };

 tri: {
 mean: number;
 std: number;

 percentiles: {
 p10: number;
 p50: number;
 p90: number;
 };
 };
 };
 };
 };
 };
 }
 ];
 };

 validation: {
 status: "incomplete" | "warning" | "valid";

 sections: {
 [sectionId: string]: {
 status: ValidationStatus;

 issues: ValidationIssue[];

 completeness: number;
 };
 };

 overall: {
 score: number;

 blockers: ValidationError[];

 warnings: ValidationWarning[];

 recommendations: string[];
 };
 };

 actions: {
 save: {
 label: "Sauvegarder";
 shortcut: "Ctrl+S";

 autosave: {
 enabled: boolean;

 interval: number;

 lastSave: Date;
 };
 };

 calculate: {
 label: "Calculer";
 shortcut: "Ctrl+Enter";

 options: {
 method: "quick" | "detailed" | "monte_carlo";

 dependencies: {
 recalculate: boolean;

 cascade: boolean;
 };
 };
 };

 duplicate: {
 label: "Dupliquer";

 options: {
 name: string;

 inherit: string[];

 modify: {
 [parameter: string]: any;
 };
 };
 };

 export: {
 label: "Exporter";

 formats: [
 {
 id: "json";
 label: "JSON";
 description: "Configuration complète";
 },
 {
 id: "xlsx";
 label: "Excel";
 description: "Paramètres et résultats";
 },
 {
 id: "pdf";
 label: "PDF";
 description: "Rapport détaillé";
 }
 ];
 };
 };
}
```

### Section Comparaison et Analyse
```typescript
interface ComparisonAnalysisSection {
 title: " Comparaison et analyse";

 comparison: {
 selection: {
 scenarios: string[];

 selector: {
 type: "multiselect" | "checkbox_list";

 options: Scenario[];

 constraints: {
 min: 2;
 max: 10;

 validation: {
 compatible: boolean;

 issues: string[];
 };
 };
 };
 };

 criteria: {
 categories: [
 {
 id: "financial";
 label: "Indicateurs financiers";

 metrics: [
 {
 id: "van";
 label: "VAN";
 unit: "€";

 importance: "high";

 display: {
 format: "currency";

 comparison: {
 type: "absolute" | "relative";

 baseline: string;
 };
 };
 },
 {
 id: "tri";
 label: "TRI";
 unit: "%";

 importance: "high";

 display: {
 format: "percentage";

 thresholds: {
 excellent: 12;
 good: 8;
 acceptable: 5;
 };
 };
 },
 {
 id: "payback";
 label: "Payback";
 unit: "ans";

 importance: "medium";

 display: {
 format: "number";

 target: {
 max: 10;

 color: "green" | "orange" | "red";
 };
 };
 }
 ];
 },
 {
 id: "technical";
 label: "Paramètres techniques";

 metrics: [
 {
 id: "power";
 label: "Puissance";
 unit: "kWc";

 importance: "medium";
 },
 {
 id: "production";
 label: "Production";
 unit: "MWh/an";

 importance: "medium";
 },
 {
 id: "pr";
 label: "Performance Ratio";
 unit: "%";

 importance: "low";
 }
 ];
 },
 {
 id: "economic";
 label: "Paramètres économiques";

 metrics: [
 {
 id: "investment";
 label: "Investissement";
 unit: "€";

 importance: "high";
 },
 {
 id: "revenue";
 label: "Revenus annuels";
 unit: "€/an";

 importance: "medium";
 },
 {
 id: "costs";
 label: "Coûts annuels";
 unit: "€/an";

 importance: "medium";
 }
 ];
 },
 {
 id: "risks";
 label: "Risques";

 metrics: [
 {
 id: "overall_risk";
 label: "Risque global";
 unit: "score";

 importance: "high";

 scale: {
 min: 0;
 max: 10;

 labels: {
 low: [0, 3];
 medium: [3, 7];
 high: [7, 10];
 };
 };
 },
 {
 id: "technical_risk";
 label: "Risque technique";
 unit: "score";

 importance: "medium";
 },
 {
 id: "financial_risk";
 label: "Risque financier";
 unit: "score";

 importance: "medium";
 }
 ];
 }
 ];

 weighting: {
 enabled: boolean;

 weights: {
 [criteriaId: string]: number;
 };

 normalization: {
 method: "sum" | "minmax" | "zscore";

 total: number;
 };
 };
 };

 visualization: {
 types: [
 {
 id: "table";
 label: "Tableau";

 features: {
 sorting: boolean;

 highlighting: {
 best: boolean;
 worst: boolean;

 thresholds: boolean;
 };

 export: boolean;
 };
 },
 {
 id: "radar";
 label: "Radar";

 features: {
 normalization: boolean;

 overlay: boolean;

 interactive: boolean;
 };
 },
 {
 id: "parallel";
 label: "Coordonnées parallèles";

 features: {
 filtering: boolean;

 brushing: boolean;

 clustering: boolean;
 };
 },
 {
 id: "scatter";
 label: "Nuage de points";

 axes: {
 x: string;
 y: string;

 size: string;
 color: string;
 };

 features: {
 regression: boolean;

 clustering: boolean;

 selection: boolean;
 };
 }
 ];

 current: {
 type: string;

 configuration: VisualizationConfig;

 interactions: {
 zoom: boolean;
 pan: boolean;

 tooltip: {
 enabled: boolean;

 content: string[];
 };

 selection: {
 enabled: boolean;

 multiple: boolean;

 actions: SelectionAction[];
 };
 };
 };
 };

 analysis: {
 ranking: {
 method: "weighted_sum" | "topsis" | "ahp";

 weighted_sum: {
 weights: {
 [criteriaId: string]: number;
 };

 results: {
 [scenarioId: string]: {
 score: number;

 rank: number;

 breakdown: {
 [criteriaId: string]: number;
 };
 };
 };
 };

 sensitivity: {
 enabled: boolean;

 parameters: string[];

 analysis: {
 [parameter: string]: {
 range: [number, number];

 impact: {
 [scenarioId: string]: number;
 };
 };
 };
 };
 };

 clustering: {
 enabled: boolean;

 method: "kmeans" | "hierarchical" | "dbscan";

 features: string[];

 results: {
 clusters: {
 [clusterId: string]: {
 scenarios: string[];

 centroid: {
 [feature: string]: number;
 };

 characteristics: string[];
 };
 };

 silhouette: number;
 };
 };

 pareto: {
 enabled: boolean;

 objectives: [
 {
 id: "van";
 label: "VAN";

 direction: "maximize";
 },
 {
 id: "risk";
 label: "Risque";

 direction: "minimize";
 }
 ];

 frontier: {
 scenarios: string[];

 dominated: string[];

 visualization: {
 type: "scatter";

 annotations: boolean;
 };
 };
 };
 };

 recommendations: {
 automatic: {
 enabled: boolean;

 criteria: {
 financial: "maximize_van" | "maximize_tri" | "minimize_payback";

 risk: "minimize_risk" | "balance_risk_return";

 constraints: Constraint[];
 };

 results: {
 best: {
 scenario: string;

 score: number;

 reasoning: string[];
 };

 alternatives: {
 scenario: string;

 score: number;

 tradeoffs: string[];
 }[];
 };
 };

 manual: {
 notes: string;

 preferences: {
 [criteriaId: string]: {
 weight: number;

 preference: "minimize" | "maximize" | "target";

 target?: number;
 };
 };

 constraints: {
 [scenarioId: string]: {
 excluded: boolean;

 reason: string;
 };
 };
 };
 };
 };

 reporting: {
 templates: [
 {
 id: "executive";
 label: "Résumé exécutif";

 sections: [
 "Synthèse comparative",
 "Recommandations",
 "Analyse des risques",
 "Conclusion"
 ];

 format: "pptx";
 },
 {
 id: "detailed";
 label: "Rapport détaillé";

 sections: [
 "Contexte et objectifs",
 "Méthodologie",
 "Description des scénarios",
 "Résultats détaillés",
 "Analyse comparative",
 "Analyse de sensibilité",
 "Recommandations",
 "Annexes"
 ];

 format: "pdf";
 },
 {
 id: "technical";
 label: "Fiche technique";

 sections: [
 "Paramètres techniques",
 "Hypothèses économiques",
 "Résultats financiers",
 "Analyse des risques"
 ];

 format: "xlsx";
 }
 ];

 generation: {
 automatic: {
 enabled: boolean;

 trigger: "on_comparison" | "on_calculation" | "manual";

 distribution: {
 email: string[];

 storage: {
 location: string;

 retention: number;
 };
 };
 };

 customization: {
 branding: {
 logo: string;

 colors: {
 primary: string;
 secondary: string;
 };
 };

 content: {
 sections: string[];

 metrics: string[];

 charts: string[];
 };
 };
 };
 };
}
```

## État et données

```typescript
interface ScenariosState {
 // Gestion des scénarios
 scenarios: {
 list: Scenario[];

 selected: string[];
 current: string;

 filters: {
 type: string[];
 status: string[];

 search: {
 query: string;
 results: string[];
 };

 range: {
 van: [number, number];
 tri: [number, number];
 risk: [number, number];
 };
 };

 sorting: {
 field: string;
 direction: "asc" | "desc";
 };
 };

 // Configuration active
 currentScenario: {
 id: string;

 metadata: ScenarioMetadata;

 parameters: {
 technical: TechnicalParameters;
 economic: EconomicParameters;
 financial: FinancialParameters;
 risks: RiskParameters;
 };

 validation: {
 status: ValidationStatus;

 sections: ValidationResults;

 issues: ValidationIssue[];
 };

 calculations: {
 status: "idle" | "calculating" | "completed" | "error";

 progress: number;

 results: ScenarioResults;
 };
 };

 // Comparaison
 comparison: {
 scenarios: string[];

 criteria: {
 selected: string[];

 weights: {
 [criteriaId: string]: number;
 };
 };

 visualization: {
 type: string;

 configuration: VisualizationConfig;
 };

 analysis: {
 ranking: RankingResults;

 clustering: ClusteringResults;

 pareto: ParetoResults;
 };

 recommendations: {
 automatic: AutomaticRecommendations;

 manual: ManualRecommendations;
 };
 };

 // Templates
 templates: {
 scenarios: ScenarioTemplate[];

 reports: ReportTemplate[];

 current: string;
 };

 // État UI
 ui: {
 view: "management" | "configuration" | "comparison";

 activeSection: string;

 modals: {
 createScenario: {
 visible: boolean;

 method: string;

 step: number;
 };

 comparison: {
 visible: boolean;

 scenarios: string[];

 configuration: ComparisonConfig;
 };

 export: {
 visible: boolean;

 format: string;

 options: ExportOptions;
 };
 };

 calculations: {
 queue: string[];

 progress: {
 [scenarioId: string]: {
 current: number;
 total: number;
 };
 };
 };
 };
}
```

## API Endpoints

```typescript
// Gestion des scénarios
GET /api/scenarios
POST /api/scenarios
PUT /api/scenarios/:id
DELETE /api/scenarios/:id

// Configuration
GET /api/scenarios/:id/configuration
PUT /api/scenarios/:id/configuration
POST /api/scenarios/:id/validate

// Calculs
POST /api/scenarios/:id/calculate
GET /api/scenarios/:id/results
POST /api/scenarios/bulk/calculate

// Comparaison
POST /api/scenarios/compare
POST /api/scenarios/analyze
GET /api/scenarios/ranking

// Templates
GET /api/templates/scenarios
POST /api/templates/scenarios
PUT /api/templates/scenarios/:id

// Export
POST /api/scenarios/export
GET /api/scenarios/:id/report
```

## Exemple d'implémentation

```tsx
import React, { useState, useEffect } from 'react';
import {
 ScenariosLayout,
 ScenarioManagement,
 ScenarioConfiguration,
 ComparisonPanel,
 AnalysisResults
} from '@/components/scenarios';

export const ScenariosPage: React.FC = () => {
 const [scenarios, setScenarios] = useState<Scenario[]>([]);
 const [currentScenario, setCurrentScenario] = useState<string>();
 const [comparison, setComparison] = useState<ComparisonState>();
 const [view, setView] = useState<'management' | 'configuration' | 'comparison'>('management');

 const handleScenarioCreate = async (method: string, data: any) => {
 const scenario = await scenariosAPI.create({
 method,
 data,
 baseline: scenarios.find(s => s.type === 'baseline')?.id
 });

 setScenarios(prev => [...prev, scenario]);
 setCurrentScenario(scenario.id);
 setView('configuration');
 };

 const handleParameterChange = (section: string, field: string, value: any) => {
 const updatedScenario = {
...currentScenario,
 parameters: {
...currentScenario.parameters,
 [section]: {
...currentScenario.parameters[section],
 [field]: value
 }
 }
 };

 setCurrentScenario(updatedScenario);

 // Validation temps réel
 validateScenario(updatedScenario);
 };

 const handleCompareScenarios = (scenarioIds: string[]) => {
 setComparison({
 scenarios: scenarioIds,
 criteria: defaultCriteria,
 visualization: { type: 'table' }
 });

 setView('comparison');
 };

 const handleCalculateScenario = async (scenarioId: string) => {
 await scenariosAPI.calculate(scenarioId);

 // Mise à jour des résultats
 loadScenarioResults(scenarioId);
 };

 return (
 <ScenariosLayout>
 {view === 'management' && (
 <ScenarioManagement
 scenarios={scenarios}
 onScenarioSelect={setCurrentScenario}
 onScenarioCreate={handleScenarioCreate}
 onScenarioCalculate={handleCalculateScenario}
 onCompareScenarios={handleCompareScenarios}
 />
 )}

 {view === 'configuration' && currentScenario && (
 <ScenarioConfiguration
 scenario={currentScenario}
 onChange={handleParameterChange}
 onCalculate={handleCalculateScenario}
 onValidate={validateScenario}
 />
 )}

 {view === 'comparison' && comparison && (
 <ComparisonPanel
 scenarios={comparison.scenarios}
 criteria={comparison.criteria}
 visualization={comparison.visualization}
 onAnalyze={runAnalysis}
 />
 )}
 </ScenariosLayout>
 );
};
```

Cette configuration des scénarios offre une approche complète pour explorer différentes variantes de projet avec des outils avancés de comparaison et d'analyse décisionnelle.