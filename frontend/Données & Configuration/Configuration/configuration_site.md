# Configuration par Site

## Vue d'ensemble

La page de configuration par site permet de gérer des projets multi-sites avec paramétrage individuel de chaque installation: localisation, caractéristiques techniques, contraintes spécifiques, et optimisation globale du portefeuille de sites.

## Structure de la page

### Header de Configuration
```typescript
interface SiteConfigurationHeader {
 title: "Configuration par Site";

 portfolio: {
 totalSites: number;
 totalPower: number;
 totalInvestment: number;

 status: {
 configured: number;
 pending: number;
 validated: number;
 };

 aggregated: {
 averageProduction: number;
 totalRevenue: number;
 portfolioRisk: number;
 };
 };

 actions: {
 addSite: {
 label: "Ajouter un site";
 icon: "add_location";
 onClick: () => void;
 };

 importSites: {
 label: "Importer sites";
 icon: "upload";
 formats: [".xlsx", ".csv", ".json"];
 onImport: (file: File) => void;
 };

 optimize: {
 label: "Optimiser portefeuille";
 icon: "tune";
 onClick: () => void;
 };

 generate: {
 label: "Générer rapport";
 icon: "description";
 onClick: () => void;
 };
 };
}
```

### Section Gestion des Sites
```typescript
interface SiteManagementSection {
 title: " Gestion des sites";

 siteList: {
 view: "table" | "cards" | "map";

 table: {
 columns: [
 {
 id: "name";
 label: "Nom du site";
 sortable: true;

 cell: {
 editable: boolean;
 validation: string[];
 };
 },
 {
 id: "location";
 label: "Localisation";
 sortable: true;

 cell: {
 display: string;
 coordinates: [number, number];

 map: {
 preview: boolean;
 onClick: () => void;
 };
 };
 },
 {
 id: "power";
 label: "Puissance";
 sortable: true;
 unit: "kWc";

 cell: {
 editable: boolean;
 validation: { min: number; max: number };
 };
 },
 {
 id: "production";
 label: "Production";
 sortable: true;
 unit: "MWh/an";

 cell: {
 calculated: boolean;
 status: "calculating" | "estimated" | "validated";
 };
 },
 {
 id: "investment";
 label: "Investissement";
 sortable: true;
 unit: "€";

 cell: {
 calculated: boolean;
 breakdown: boolean;
 };
 },
 {
 id: "status";
 label: "Statut";
 sortable: true;

 cell: {
 type: "badge";
 color: string;

 options: [
 { value: "draft", label: "Brouillon", color: "gray" },
 { value: "configured", label: "Configuré", color: "blue" },
 { value: "validated", label: "Validé", color: "green" },
 { value: "error", label: "Erreur", color: "red" }
 ];
 };
 },
 {
 id: "actions";
 label: "Actions";

 buttons: [
 {
 icon: "edit";
 label: "Modifier";
 onClick: (site: Site) => void;
 },
 {
 icon: "content_copy";
 label: "Dupliquer";
 onClick: (site: Site) => void;
 },
 {
 icon: "delete";
 label: "Supprimer";
 onClick: (site: Site) => void;
 confirm: true;
 }
 ];
 }
 ];

 data: Site[];

 pagination: {
 page: number;
 pageSize: number;
 total: number;
 };

 filters: {
 status: string[];
 powerRange: { min: number; max: number };
 location: string[];

 search: {
 query: string;
 fields: string[];
 };
 };

 sorting: {
 field: string;
 direction: "asc" | "desc";
 };
 };

 cards: {
 layout: "grid" | "list";

 card: {
 header: {
 name: string;
 status: SiteStatus;
 actions: Action[];
 };

 content: {
 location: {
 display: string;
 coordinates: [number, number];

 map: {
 thumbnail: boolean;
 interactive: boolean;
 };
 };

 metrics: {
 power: number;
 production: number;
 investment: number;

 indicators: {
 roi: number;
 payback: number;
 risk: number;
 };
 };

 progress: {
 configuration: number;
 validation: number;

 nextsteps: string[];
 };
 };

 footer: {
 lastModified: Date;
 createdBy: string;

 quickActions: QuickAction[];
 };
 };
 };

 map: {
 provider: "leaflet" | "mapbox" | "google";

 layers: [
 {
 id: "sites";
 label: "Sites";
 visible: true;

 markers: {
 style: "cluster" | "individual";

 cluster: {
 enabled: boolean;
 radius: number;
 maxZoom: number;
 };

 individual: {
 icon: string;
 color: string;
 size: number;

 status: {
 draft: { color: "gray", icon: "location_on" };
 configured: { color: "blue", icon: "location_on" };
 validated: { color: "green", icon: "location_on" };
 error: { color: "red", icon: "error" };
 };
 };
 };

 popup: {
 content: SiteMapPopup;

 actions: [
 { label: "Voir détails", onClick: () => void },
 { label: "Modifier", onClick: () => void }
 ];
 };
 },
 {
 id: "irradiation";
 label: "Irradiation";
 visible: false;

 heatmap: {
 source: "PVGIS";
 opacity: 0.7;

 legend: {
 min: number;
 max: number;
 unit: "kWh/m²/an";
 };
 };
 },
 {
 id: "infrastructure";
 label: "Infrastructure";
 visible: false;

 features: [
 "Lignes électriques",
 "Postes de transformation",
 "Réseaux transport"
 ];
 }
 ];

 tools: {
 measurement: boolean;
 drawing: boolean;

 analysis: {
 distance: boolean;
 coverage: boolean;
 optimization: boolean;
 };
 };

 interaction: {
 onClick: (coordinates: [number, number]) => void;
 onDraw: (geometry: Geometry) => void;

 selection: {
 multiple: boolean;
 actions: SelectionAction[];
 };
 };
 };
 };

 bulkActions: {
 label: "Actions groupées";

 selection: {
 all: boolean;
 sites: string[];

 actions: [
 {
 id: "bulk_edit";
 label: "Modifier en lot";
 icon: "edit";

 fields: [
 "technology",
 "installationType",
 "financing",
 "tariff"
 ];

 onClick: (sites: string[]) => void;
 },
 {
 id: "bulk_calculate";
 label: "Calculer production";
 icon: "calculate";

 onClick: (sites: string[]) => void;
 },
 {
 id: "bulk_validate";
 label: "Valider";
 icon: "check_circle";

 onClick: (sites: string[]) => void;
 },
 {
 id: "bulk_export";
 label: "Exporter";
 icon: "download";

 formats: ["xlsx", "csv", "pdf"];

 onClick: (sites: string[], format: string) => void;
 }
 ];
 };
 };
}
```

### Section Configuration Individuelle
```typescript
interface IndividualSiteConfiguration {
 title: " Configuration individuelle";

 siteSelection: {
 current: string;

 selector: {
 type: "dropdown" | "tabs";

 options: Site[];

 search: {
 enabled: boolean;
 placeholder: "Rechercher un site...";
 };

 grouping: {
 enabled: boolean;
 by: "region" | "status" | "type";
 };
 };

 navigation: {
 previous: () => void;
 next: () => void;

 shortcuts: {
 enabled: boolean;
 keys: string[];
 };
 };
 };

 siteDetails: {
 header: {
 name: {
 label: "Nom du site";
 type: "text";
 value: string;

 validation: {
 required: boolean;
 unique: boolean;
 pattern: RegExp;
 };
 };

 reference: {
 label: "Référence";
 type: "text";
 value: string;

 generation: {
 auto: boolean;
 template: string;
 };
 };

 priority: {
 label: "Priorité";
 type: "select";
 value: string;

 options: [
 { value: "high", label: "Haute", color: "red" },
 { value: "medium", label: "Moyenne", color: "orange" },
 { value: "low", label: "Basse", color: "green" }
 ];
 };
 };

 location: {
 label: "Localisation";

 address: {
 type: "address";
 value: Address;

 geocoding: {
 provider: "google" | "here" | "nominatim";

 onSelect: (address: Address) => {
 coordinates: [number, number];

 automatic: {
 irradiation: number;
 temperature: number;
 windZone: string;
 };
 };
 };
 };

 coordinates: {
 label: "Coordonnées";
 type: "coordinates";
 value: [number, number];

 precision: {
 decimal: number;
 system: "WGS84" | "Lambert93";
 };

 validation: {
 bounds: GeoBounds;
 accuracy: number;
 };
 };

 map: {
 visible: boolean;

 center: [number, number];
 zoom: number;

 markers: {
 site: {
 draggable: boolean;
 onDragEnd: (coordinates: [number, number]) => void;
 };
 };

 layers: [
 "satellite",
 "cadastre",
 "irradiation",
 "obstacles"
 ];

 tools: {
 measurement: boolean;
 drawing: boolean;

 analysis: {
 shading: boolean;
 suitability: boolean;
 };
 };
 };
 };

 installation: {
 label: "Caractéristiques installation";

 type: {
 label: "Type d'installation";
 type: "select";
 value: string;

 options: InstallationType[];

 onChange: (type: string) => {
 // Mise à jour champs conditionnels
 updateConditionalFields(type);
 };
 };

 power: {
 label: "Puissance crête";
 type: "number";
 value: number;
 unit: "kWc";

 validation: {
 min: 0.1;
 max: 10000;

 warnings: {
 underSized: boolean;
 overSized: boolean;
 };
 };

 calculator: {
 enabled: boolean;

 fromPanels: {
 quantity: number;
 unitPower: number;

 result: number;
 };

 fromArea: {
 area: number;
 density: number;

 result: number;
 };
 };
 };

 technology: {
 label: "Technologie";
 type: "select";
 value: string;

 options: Technology[];

 impact: {
 onPerformance: number;
 onCost: number;
 onDegradation: number;
 };
 };

 orientation: {
 label: "Orientation";
 type: "compass";
 value: number;
 unit: "°";

 optimal: {
 calculate: boolean;
 value: number;

 deviation: {
 current: number;
 impact: number;
 };
 };
 };

 inclination: {
 label: "Inclinaison";
 type: "slider";
 value: number;
 unit: "°";

 range: {
 min: 0;
 max: 90;

 optimal: {
 latitude: number;
 recommended: number;
 };
 };
 };

 specificConfig: {
 label: "Configuration spécifique";

 conditional: {
 [installationType: string]: {
 fields: ConditionalField[];

 validation: ValidationRule[];
 };
 };

 toitureInclinee: {
 materiauCouverture: {
 label: "Matériau couverture";
 type: "select";
 options: CoverMaterial[];
 };

 typeFixation: {
 label: "Type fixation";
 type: "select";
 options: FixationType[];
 };

 penetrationEtancheite: {
 label: "Pénétration étanchéité";
 type: "toggle";
 value: boolean;
 };
 };

 toitureRampante: {
 penteMinimum: {
 label: "Pente minimum";
 type: "number";
 value: number;
 unit: "°";
 };

 typeSupport: {
 label: "Type support";
 type: "select";
 options: SupportType[];
 };

 lestage: {
 label: "Lestage";
 type: "toggle";
 value: boolean;

 details: {
 poids: number;
 type: string;
 };
 };
 };

 ombriere: {
 hauteurLibre: {
 label: "Hauteur libre";
 type: "number";
 value: number;
 unit: "m";

 validation: {
 min: 2.5;
 max: 4.5;
 };
 };

 nombrePlaces: {
 label: "Nombre de places";
 type: "number";
 value: number;

 calculation: {
 surface: number;
 ratio: number;
 };
 };

 structureType: {
 label: "Type structure";
 type: "select";
 options: StructureType[];
 };
 };

 sol: {
 surface: {
 label: "Surface disponible";
 type: "number";
 value: number;
 unit: "m²";
 };

 typeSol: {
 label: "Type de sol";
 type: "select";
 options: SoilType[];
 };

 pente: {
 label: "Pente terrain";
 type: "number";
 value: number;
 unit: "%";
 };

 contraintes: {
 label: "Contraintes";
 type: "multi-select";
 options: Constraint[];
 };
 };
 };
 };

 environmental: {
 label: "Données environnementales";

 irradiation: {
 label: "Irradiation";

 source: {
 type: "select";
 value: string;

 options: [
 { value: "pvgis", label: "PVGIS" },
 { value: "meteonorm", label: "Meteonorm" },
 { value: "custom", label: "Personnalisée" }
 ];
 };

 annual: {
 label: "Irradiation annuelle";
 type: "number";
 value: number;
 unit: "kWh/m²/an";

 automatic: {
 enabled: boolean;
 source: string;

 update: {
 onLocationChange: boolean;
 onOrientationChange: boolean;
 };
 };
 };

 monthly: {
 label: "Répartition mensuelle";
 type: "monthly-data";
 value: number[];

 visualization: {
 type: "bar" | "line";
 comparison: boolean;
 };
 };
 };

 temperature: {
 label: "Température";

 average: {
 label: "Température moyenne";
 type: "number";
 value: number;
 unit: "°C";
 };

 range: {
 label: "Plage de températures";
 type: "range";
 value: [number, number];
 unit: "°C";

 impact: {
 onPerformance: number;
 onDegradation: number;
 };
 };
 };

 obstacles: {
 label: "Obstacles et masques";

 list: [
 {
 id: string;
 type: "building" | "tree" | "terrain" | "structure";
 name: string;

 geometry: {
 height: number;
 distance: number;
 angle: number;

 coordinates: [number, number][];
 };

 impact: {
 shading: number;
 periods: TimePeriod[];
 };

 seasonal: {
 winter: number;
 summer: number;
 };
 }
 ];

 analysis: {
 method: "geometric" | "simulation";

 results: {
 totalLoss: number;
 monthlyLoss: number[];

 visualization: {
 type: "heatmap" | "chart";
 exportable: boolean;
 };
 };
 };
 };
 };

 economics: {
 label: "Paramètres économiques";

 investment: {
 method: "global" | "specific";

 global: {
 usePortfolio: boolean;

 costsPerKwc: number;

 economies: {
 scale: number;
 procurement: number;
 logistics: number;
 };
 };

 specific: {
 detailed: boolean;

 categories: CostCategory[];

 total: number;
 };
 };

 revenue: {
 contractType: string;

 tariff: {
 rate: number;
 duration: number;
 indexation: IndexationConfig;
 };

 autoconsommation: {
 enabled: boolean;
 rate: number;

 savings: {
 annual: number;
 evolution: number;
 };
 };
 };

 financing: {
 usePortfolio: boolean;

 specific: {
 equity: number;
 debt: DebtConfig;

 subsidies: Aid[];
 };
 };
 };

 risks: {
 label: "Risques spécifiques";

 technical: [
 {
 id: "shading";
 label: "Ombrage";
 level: "low" | "medium" | "high";

 mitigation: [
 "Optimisation layout",
 "Micro-onduleurs",
 "Élagage"
 ];
 },
 {
 id: "access";
 label: "Accès maintenance";
 level: "low" | "medium" | "high";

 mitigation: [
 "Chemin d'accès",
 "Équipement spécialisé",
 "Planification"
 ];
 }
 ];

 regulatory: [
 {
 id: "planning";
 label: "Autorisation urbanisme";
 level: "low" | "medium" | "high";

 status: "obtained" | "pending" | "required";

 mitigation: [
 "Étude préalable",
 "Concertation",
 "Plan B"
 ];
 }
 ];

 financial: [
 {
 id: "grid_connection";
 label: "Raccordement réseau";
 level: "low" | "medium" | "high";

 cost: {
 estimated: number;
 confirmed: boolean;
 };

 timeline: {
 estimated: number;
 confirmed: boolean;
 };
 }
 ];
 };

 validation: {
 label: "Validation";

 sections: {
 location: ValidationResult;
 installation: ValidationResult;
 environmental: ValidationResult;
 economics: ValidationResult;
 risks: ValidationResult;
 };

 overall: {
 status: "incomplete" | "warnings" | "valid";
 score: number;

 blockers: ValidationError[];
 warnings: ValidationWarning[];

 nextSteps: string[];
 };
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

 duplicate: {
 label: "Dupliquer site";

 options: {
 name: string;
 copyData: string[];

 modifications: {
 location: boolean;
 power: boolean;
 other: boolean;
 };
 };
 };

 template: {
 label: "Créer template";

 options: {
 name: string;
 description: string;

 include: string[];

 sharing: {
 level: "private" | "team" | "public";
 };
 };
 };

 calculate: {
 label: "Calculer production";

 options: {
 method: "quick" | "detailed";

 update: {
 economics: boolean;
 portfolio: boolean;
 };
 };
 };
 };
}
```

### Section Optimisation Portefeuille
```typescript
interface PortfolioOptimizationSection {
 title: " Optimisation portefeuille";

 objectives: {
 label: "Objectifs d'optimisation";

 primary: {
 type: "maximize_return" | "minimize_risk" | "balance";

 maximize_return: {
 metric: "van" | "tri" | "revenue";
 target: number;

 constraints: {
 maxRisk: number;
 maxInvestment: number;
 minDiversification: number;
 };
 };

 minimize_risk: {
 metric: "volatility" | "correlation" | "concentration";
 target: number;

 constraints: {
 minReturn: number;
 maxSites: number;
 };
 };

 balance: {
 returnWeight: number;
 riskWeight: number;

 frontiere: {
 points: number;

 results: {
 return: number;
 risk: number;
 allocation: SiteAllocation[];
 }[];
 };
 };
 };

 secondary: {
 geographical: {
 diversification: boolean;
 concentration: boolean;

 regions: {
 preferred: string[];
 avoided: string[];

 limits: {
 maxPerRegion: number;
 minSpread: number;
 };
 };
 };

 technical: {
 technology: {
 diversification: boolean;

 mix: {
 monocrystalline: number;
 polycrystalline: number;
 bifacial: number;
 };
 };

 installationType: {
 diversification: boolean;

 mix: {
 rooftop: number;
 ground: number;
 carport: number;
 };
 };
 };

 scale: {
 siteSize: {
 min: number;
 max: number;

 distribution: {
 small: number;
 medium: number;
 large: number;
 };
 };

 totalPortfolio: {
 min: number;
 max: number;

 tranches: {
 target: number;
 tolerance: number;
 };
 };
 };
 };
 };

 constraints: {
 label: "Contraintes";

 financial: {
 totalBudget: {
 limit: number;
 allocated: number;

 flexibility: {
 percentage: number;
 conditions: string[];
 };
 };

 financing: {
 maxDebtRatio: number;
 minEquityRatio: number;

 diversification: {
 sources: string[];
 limits: number[];
 };
 };

 returns: {
 minTri: number;
 minVan: number;

 hurdle: {
 rate: number;
 adjustments: RiskAdjustment[];
 };
 };
 };

 operational: {
 capacity: {
 simultaneousSites: number;

 phases: {
 development: number;
 construction: number;
 operation: number;
 };
 };

 resources: {
 teams: number;
 subcontractors: number;

 skills: {
 required: string[];
 available: string[];
 };
 };

 timeline: {
 maxDuration: number;

 milestones: {
 development: number;
 construction: number;
 commissioning: number;
 };
 };
 };

 regulatory: {
 authorizations: {
 simultaneous: number;

 complexity: {
 simple: number;
 complex: number;
 };
 };

 grid: {
 connectionCapacity: number;

 constraints: {
 voltage: string[];
 distance: number;
 };
 };
 };
 };

 analysis: {
 label: "Analyse du portefeuille";

 current: {
 metrics: {
 totalReturn: number;
 weightedRisk: number;

 diversification: {
 geographical: number;
 technical: number;
 scale: number;
 };

 correlation: {
 matrix: number[][];
 average: number;
 };
 };

 composition: {
 bySite: SiteAllocation[];
 byRegion: RegionAllocation[];
 byTechnology: TechnologyAllocation[];

 concentration: {
 top3: number;
 top5: number;
 hhi: number;
 };
 };
 };

 scenarios: {
 label: "Scénarios";

 list: [
 {
 id: "optimized";
 name: "Optimisé";

 allocation: SiteAllocation[];

 metrics: {
 totalReturn: number;
 totalRisk: number;

 improvement: {
 returnGain: number;
 riskReduction: number;
 };
 };

 changes: {
 sitesToAdd: Site[];
 sitesToRemove: Site[];
 sitesToModify: SiteModification[];
 };
 },
 {
 id: "conservative";
 name: "Conservateur";

 allocation: SiteAllocation[];

 characteristics: {
 lowerRisk: boolean;
 lowerReturn: boolean;

 diversification: "high";
 concentration: "low";
 };
 },
 {
 id: "aggressive";
 name: "Agressif";

 allocation: SiteAllocation[];

 characteristics: {
 higherRisk: boolean;
 higherReturn: boolean;

 concentration: "high";
 leverage: "high";
 };
 }
 ];

 comparison: {
 criteria: string[];

 matrix: {
 [scenario: string]: {
 [criterion: string]: number;
 };
 };

 recommendation: {
 best: string;
 reasoning: string;

 conditions: string[];
 };
 };
 };

 sensitivity: {
 label: "Analyse de sensibilité";

 parameters: [
 {
 name: "Irradiation";
 variation: number;

 impact: {
 onReturn: number;
 onRisk: number;

 bySite: SiteImpact[];
 };
 },
 {
 name: "Tarif électricité";
 variation: number;

 impact: {
 onReturn: number;
 onRisk: number;
 };
 },
 {
 name: "Coût investissement";
 variation: number;

 impact: {
 onReturn: number;
 onRisk: number;
 };
 }
 ];

 results: {
 worstCase: PortfolioResult;
 bestCase: PortfolioResult;

 robustness: {
 score: number;

 resilience: {
 toShocks: number;
 toChanges: number;
 };
 };
 };
 };
 };

 optimization: {
 label: "Optimisation";

 algorithm: {
 type: "genetic" | "simulated_annealing" | "gradient";

 parameters: {
 iterations: number;
 population: number;
 mutation: number;

 convergence: {
 tolerance: number;
 maxIterations: number;
 };
 };
 };

 execution: {
 status: "idle" | "running" | "completed" | "error";

 progress: {
 current: number;
 total: number;

 eta: number;

 intermediate: {
 results: OptimizationResult[];

 bestSoFar: {
 objective: number;
 allocation: SiteAllocation[];
 };
 };
 };
 };

 results: {
 label: "Résultats";

 optimal: {
 allocation: SiteAllocation[];

 metrics: {
 objective: number;
 return: number;
 risk: number;

 constraints: {
 satisfied: boolean;
 violations: ConstraintViolation[];
 };
 };

 improvement: {
 vs_current: {
 return: number;
 risk: number;

 significance: "minor" | "moderate" | "major";
 };

 vs_naive: {
 return: number;
 risk: number;
 };
 };
 };

 alternatives: {
 label: "Alternatives";

 list: OptimizationResult[];

 comparison: {
 criteria: string[];

 ranking: {
 byReturn: OptimizationResult[];
 byRisk: OptimizationResult[];
 byRatio: OptimizationResult[];
 };
 };
 };
 };
 };
}
```

## État et données

```typescript
interface SiteConfigurationState {
 // Gestion des sites
 sites: {
 list: Site[];

 selected: string[];
 current: string;

 filters: {
 status: string[];
 powerRange: [number, number];
 location: string[];

 search: {
 query: string;
 results: string[];
 };
 };

 sorting: {
 field: string;
 direction: "asc" | "desc";
 };

 pagination: {
 page: number;
 pageSize: number;
 total: number;
 };
 };

 // Configuration active
 currentSite: {
 id: string;
 config: SiteConfiguration;

 validation: {
 status: ValidationStatus;
 sections: ValidationResults;

 blockers: ValidationError[];
 warnings: ValidationWarning[];
 };

 calculations: {
 production: ProductionResults;
 economics: EconomicResults;

 status: "idle" | "calculating" | "completed" | "error";
 };
 };

 // Portefeuille
 portfolio: {
 summary: PortfolioSummary;

 optimization: {
 objectives: OptimizationObjectives;
 constraints: OptimizationConstraints;

 scenarios: OptimizationScenario[];

 results: {
 current: OptimizationResult;
 optimal: OptimizationResult;

 comparison: ComparisonMatrix;
 };
 };

 analysis: {
 metrics: PortfolioMetrics;
 composition: PortfolioComposition;

 risks: {
 concentration: ConcentrationRisk;
 correlation: CorrelationRisk;
 operational: OperationalRisk;
 };
 };
 };

 // État UI
 ui: {
 view: "table" | "cards" | "map";

 activeSection: string;

 modals: {
 addSite: boolean;
 bulkEdit: boolean;
 optimization: boolean;

 siteDetails: {
 visible: boolean;
 siteId: string;
 tab: string;
 };
 };

 map: {
 center: [number, number];
 zoom: number;

 layers: {
 [layerId: string]: {
 visible: boolean;
 opacity: number;
 };
 };

 selection: {
 sites: string[];
 drawing: boolean;
 };
 };
 };

 // Données de référence
 reference: {
 technologies: Technology[];
 installationTypes: InstallationType[];

 regions: Region[];

 templates: SiteTemplate[];

 costs: {
 perKwc: CostData[];
 breakdown: CostBreakdown[];
 };
 };
}
```

## API Endpoints

```typescript
// Gestion des sites
GET /api/sites
POST /api/sites
PUT /api/sites/:id
DELETE /api/sites/:id

// Configuration site
GET /api/sites/:id/config
PUT /api/sites/:id/config

// Calculs par site
POST /api/sites/:id/calculate/production
POST /api/sites/:id/calculate/economics

// Portefeuille
GET /api/portfolio/summary
POST /api/portfolio/optimize
GET /api/portfolio/analysis

// Actions groupées
POST /api/sites/bulk/calculate
POST /api/sites/bulk/validate
POST /api/sites/bulk/export

// Templates
GET /api/templates/sites
POST /api/templates/sites
```

## Exemple d'implémentation

```tsx
import React, { useState, useEffect } from 'react';
import {
 SiteConfigurationLayout,
 SiteList,
 SiteEditor,
 PortfolioOptimizer,
 MapView
} from '@/components/sites';

export const SiteConfigurationPage: React.FC = () => {
 const [sites, setSites] = useState<Site[]>([]);
 const [currentSite, setCurrentSite] = useState<string>();
 const [view, setView] = useState<'table' | 'cards' | 'map'>('table');
 const [portfolio, setPortfolio] = useState<PortfolioData>();

 const handleSiteSelect = (siteId: string) => {
 setCurrentSite(siteId);
 // Chargement configuration
 loadSiteConfiguration(siteId);
 };

 const handleBulkAction = (action: string, siteIds: string[]) => {
 switch (action) {
 case 'calculate':
 calculateProductionBulk(siteIds);
 break;
 case 'validate':
 validateSitesBulk(siteIds);
 break;
 case 'export':
 exportSitesBulk(siteIds);
 break;
 }
 };

 const optimizePortfolio = async () => {
 const results = await portfolioAPI.optimize({
 sites: sites,
 objectives: portfolio.objectives,
 constraints: portfolio.constraints
 });

 setPortfolio(prev => ({
...prev,
 optimization: results
 }));
 };

 return (
 <SiteConfigurationLayout>
 <SiteList
 sites={sites}
 view={view}
 onViewChange={setView}
 onSiteSelect={handleSiteSelect}
 onBulkAction={handleBulkAction}
 />

 {currentSite && (
 <SiteEditor
 siteId={currentSite}
 onSave={handleSiteSave}
 onCalculate={handleSiteCalculate}
 />
 )}

 <PortfolioOptimizer
 portfolio={portfolio}
 onOptimize={optimizePortfolio}
 />

 {view === 'map' && (
 <MapView
 sites={sites}
 onSiteSelect={handleSiteSelect}
 onMapUpdate={handleMapUpdate}
 />
 )}
 </SiteConfigurationLayout>
 );
};
```

Cette configuration par site permet une gestion complète des projets multi-sites avec optimisation du portefeuille global et outils avancés de visualisation et d'analyse.