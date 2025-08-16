# Page Tarification Clients - Module ERP Client

## Vue d'ensemble

La page de tarification permet de gérer les grilles tarifaires, définir des tarifs personnalisés par client, simuler des factures et analyser la rentabilité avec des outils de calcul avancés et des règles métier complexes.

## Structure de la page

### Header Principal
```typescript
interface PricingHeader {
 title: " Tarification Clients";

 navigation: {
 tabs: [
 { id: "grids", label: "Grilles tarifaires", icon: "grid_on", badge?: number },
 { id: "clients", label: "Tarifs clients", icon: "person", badge?: number },
 { id: "simulator", label: "Simulateur", icon: "calculate" },
 { id: "analysis", label: "Analyse", icon: "analytics" },
 { id: "history", label: "Historique", icon: "history" }
 ];
 activeTab: string;
 onChange: (tabId: string) => void;
 };

 actions: {
 newGridButton: {
 label: "Nouvelle grille";
 icon: "add";
 variant: "primary";
 onClick: () => void;
 permissions: ["pricing:create"];
 };

 importButton: {
 label: "Importer";
 icon: "upload";
 formats: ["Excel", "CSV"];
 onImport: (file: File) => void;
 };

 settingsButton: {
 label: "Paramètres";
 icon: "settings";
 onClick: () => void;
 };
 };
}
```

### Onglet Grilles Tarifaires
```typescript
interface PricingGridsTab {
 filters: {
 search: {
 placeholder: "Rechercher une grille...";
 value: string;
 onChange: (value: string) => void;
 };

 status: {
 options: ["active", "draft", "archived"];
 value: string[];
 onChange: (status: string[]) => void;
 };

 type: {
 options: ["production", "consommation", "services", "abonnement"];
 value: string[];
 onChange: (types: string[]) => void;
 };

 validity: {
 options: ["current", "future", "expired"];
 value: string;
 onChange: (validity: string) => void;
 };
 };

 gridList: {
 layout: "cards" | "table";

 items: PricingGrid[];

 gridCard: {
 header: {
 name: string;
 code: string;
 status: {
 value: "active" | "draft" | "archived";
 color: string;
 icon: string;
 };
 type: {
 label: string;
 icon: string;
 };
 };

 body: {
 description: string;
 validity: {
 start: Date;
 end: Date | null;
 isValid: boolean;
 };

 summary: {
 basePrice: number;
 priceRanges: number;
 conditions: number;
 clientsCount: number;
 };

 preview: {
 chart: {
 type: "line" | "stepped";
 data: PricePoint[];
 showBreakpoints: boolean;
 };
 };
 };

 footer: {
 lastModified: Date;
 modifiedBy: string;

 actions: [
 { icon: "visibility", label: "Voir", onClick: () => void },
 { icon: "edit", label: "Modifier", onClick: () => void },
 { icon: "content_copy", label: "Dupliquer", onClick: () => void },
 { icon: "group", label: "Clients", badge: number, onClick: () => void },
 { icon: "archive", label: "Archiver", onClick: () => void }
 ];
 };
 };
 };

 gridCreation: {
 modal: boolean;

 form: {
 basics: {
 name: string;
 code: string;
 type: GridType;
 description: string;
 validity: {
 start: Date;
 end?: Date;
 };
 };

 structure: {
 pricingModel: {
 type: "fixed" | "variable" | "tiered" | "volume" | "package";

 configuration: {
 fixed: {
 price: number;
 unit: string;
 };

 variable: {
 formula: string;
 parameters: Parameter[];
 examples: CalculationExample[];
 };

 tiered: {
 tiers: Array<{
 min: number;
 max: number | null;
 price: number;
 unit: string;
 }>;
 cumulative: boolean;
 };

 volume: {
 brackets: Array<{
 min: number;
 max: number | null;
 price: number;
 discount?: number;
 }>;
 };

 package: {
 included: number;
 basePrice: number;
 overage: number;
 };
 };
 };

 components: Array<{
 id: string;
 name: string;
 type: "base" | "variable" | "tax" | "fee";
 calculation: string;
 optional: boolean;
 conditions: Condition[];
 }>;

 rules: {
 minimumCharge?: number;
 maximumCharge?: number;
 roundingRule: "up" | "down" | "nearest";
 roundingPrecision: number;
 taxIncluded: boolean;
 };
 };

 conditions: {
 eligibility: {
 clientTypes: ClientType[];
 zones: string[];
 tags: string[];
 customRules: Rule[];
 };

 temporalConditions: {
 seasons: Season[];
 timeOfUse: TimeOfUseRate[];
 peakHours: PeakHourDefinition[];
 };

 volumeConditions: {
 minimumVolume?: number;
 commitments: Commitment[];
 bonuses: VolumeBonus[];
 };
 };

 simulation: {
 testCases: TestCase[];
 results: SimulationResult[];
 validation: ValidationStatus;
 };
 };
 };
}
```

### Onglet Tarifs Clients
```typescript
interface ClientPricingTab {
 clientSelector: {
 search: {
 placeholder: "Rechercher un client...";
 value: string;
 onChange: (value: string) => void;
 suggestions: Client[];
 };

 selected: Client | null;

 quickInfo: {
 visible: boolean;
 data: {
 type: ClientType;
 consumption: number;
 production: number;
 currentPricing: PricingSummary;
 };
 };
 };

 pricingManagement: {
 currentPricing: {
 grid: PricingGrid | null;
 customRates: CustomRate[];
 effectiveDate: Date;
 expiryDate?: Date;

 summary: {
 averagePrice: number;
 monthlyEstimate: number;
 yearlyEstimate: number;
 margin: number;
 };

 breakdown: {
 components: PriceComponent[];
 visualize: {
 type: "pie" | "bar" | "waterfall";
 interactive: boolean;
 };
 };
 };

 actions: {
 assignGrid: {
 label: "Assigner grille";
 icon: "grid_on";
 onClick: () => void;

 modal: {
 availableGrids: PricingGrid[];
 comparison: GridComparison;
 effectiveDate: Date;
 notifications: {
 client: boolean;
 internal: string[];
 };
 };
 };

 customizeRate: {
 label: "Personnaliser";
 icon: "tune";
 onClick: () => void;

 options: {
 override: {
 type: "percentage" | "fixed" | "formula";
 components: string[];
 value: number | string;
 reason: string;
 approval: ApprovalWorkflow;
 };

 exceptions: {
 periods: DateRange[];
 volumes: VolumeRange[];
 conditions: Condition[];
 };

 incentives: {
 type: "discount" | "rebate" | "credit";
 trigger: string;
 value: number;
 duration: Duration;
 };
 };
 };

 simulate: {
 label: "Simuler";
 icon: "calculate";
 onClick: () => void;
 };

 history: {
 label: "Historique";
 icon: "history";
 onClick: () => void;
 };
 };

 bulkOperations: {
 visible: boolean;

 selection: {
 mode: "manual" | "filter";
 count: number;
 clients: Client[];
 };

 actions: [
 {
 id: "assign_grid";
 label: "Assigner grille";
 icon: "grid_on";
 confirmation: boolean;
 },
 {
 id: "apply_discount";
 label: "Appliquer remise";
 icon: "discount";
 parameters: DiscountParams;
 },
 {
 id: "update_rates";
 label: "Mettre à jour tarifs";
 icon: "update";
 dangerous: boolean;
 },
 {
 id: "export";
 label: "Exporter";
 icon: "download";
 formats: ["Excel", "PDF"];
 }
 ];

 preview: {
 enabled: boolean;
 changes: PricingChange[];
 impact: ImpactAnalysis;
 };
 };
 };
}
```

### Onglet Simulateur
```typescript
interface PricingSimulatorTab {
 configuration: {
 scenario: {
 title: string;
 description: string;

 client: {
 type: ClientType;
 profile: ConsumptionProfile;
 location: string;

 selection: {
 mode: "existing" | "new" | "template";
 client?: Client;
 template?: ClientTemplate;
 };
 };

 parameters: {
 consumption: {
 annual: number;
 monthly: number[];
 hourly: HourlyProfile;

 presets: [
 { label: "Résidentiel standard", value: "residential_std" },
 { label: "Résidentiel chauffage élec", value: "residential_heat" },
 { label: "Tertiaire", value: "commercial" },
 { label: "Industriel", value: "industrial" }
 ];

 advanced: {
 peakDemand: number;
 loadFactor: number;
 seasonality: SeasonalFactors;
 };
 };

 production: {
 enabled: boolean;
 capacity: number;
 profile: ProductionProfile;
 selfConsumption: number;

 technology: {
 type: "solar" | "wind" | "other";
 efficiency: number;
 degradation: number;
 };
 };

 grid: {
 selection: PricingGrid | null;
 alternatives: PricingGrid[];

 comparison: {
 enabled: boolean;
 grids: PricingGrid[];
 showDifferences: boolean;
 };
 };
 };
 };
 };

 simulation: {
 controls: {
 timeframe: {
 options: ["month", "year", "custom"];
 value: string;
 customRange?: DateRange;
 };

 runButton: {
 label: "Lancer simulation";
 icon: "play_arrow";
 loading: boolean;
 onClick: () => void;
 };

 saveButton: {
 label: "Sauvegarder";
 icon: "save";
 onClick: () => void;
 };

 shareButton: {
 label: "Partager";
 icon: "share";
 onClick: () => void;
 };
 };

 results: {
 summary: {
 totalCost: number;
 averagePrice: number;
 breakdown: {
 energy: number;
 capacity: number;
 taxes: number;
 fees: number;
 };

 comparison: {
 previousPeriod: number;
 marketAverage: number;
 savings: number;
 };
 };

 visualizations: {
 costEvolution: {
 type: "line";
 data: TimeSeriesData[];
 annotations: Event[];

 options: {
 granularity: "hour" | "day" | "month";
 showComponents: boolean;
 interactive: boolean;
 };
 };

 billPreview: {
 type: "document";
 template: "standard" | "detailed";

 sections: [
 { id: "header", data: BillHeader },
 { id: "consumption", data: ConsumptionDetails },
 { id: "charges", data: ChargeBreakdown },
 { id: "summary", data: BillSummary }
 ];

 actions: {
 download: () => void;
 print: () => void;
 customize: () => void;
 };
 };

 sensitivity: {
 type: "heatmap";

 variables: [
 { name: "consumption", range: [-20, 20], step: 5 },
 { name: "price", range: [-10, 10], step: 2 }
 ];

 results: SensitivityMatrix;

 insights: {
 breakeven: number;
 optimal: OptimalPoint;
 risks: Risk[];
 };
 };
 };

 recommendations: {
 optimization: Recommendation[];
 alternatives: Alternative[];
 actions: SuggestedAction[];
 };
 };

 scenarios: {
 comparison: {
 enabled: boolean;
 scenarios: Scenario[];

 view: {
 type: "table" | "chart";
 metrics: string[];
 highlight: "best" | "worst" | "differences";
 };

 export: {
 format: "excel" | "pdf" | "powerpoint";
 includeDetails: boolean;
 };
 };
 };
 };
}
```

### Onglet Analyse
```typescript
interface PricingAnalysisTab {
 metrics: {
 overview: {
 kpis: [
 {
 label: "Revenu moyen par client";
 value: number;
 trend: Trend;
 sparkline: number[];
 },
 {
 label: "Marge moyenne";
 value: number;
 format: "percentage";
 target: number;
 status: "above" | "below" | "on-target";
 },
 {
 label: "Taux d'adoption nouvelles grilles";
 value: number;
 format: "percentage";
 timeframe: "30 days";
 },
 {
 label: "Clients sous-optimaux";
 value: number;
 action: { label: "Voir", onClick: () => void };
 }
 ];
 };

 profitability: {
 title: "Analyse de rentabilité";

 segments: {
 dimension: "client_type" | "pricing_grid" | "zone" | "volume";

 data: Array<{
 segment: string;
 revenue: number;
 cost: number;
 margin: number;
 marginRate: number;
 clients: number;
 trend: Trend;
 }>;

 visualization: {
 type: "bubble" | "treemap" | "sunburst";
 size: "revenue" | "margin" | "clients";
 color: "margin_rate" | "growth" | "segment";
 };

 actions: {
 drillDown: (segment: string) => void;
 export: () => void;
 optimize: (segment: string) => void;
 };
 };

 distribution: {
 title: "Distribution des marges";

 histogram: {
 data: MarginDistribution[];
 bins: number;

 annotations: [
 { value: number; label: "Moyenne" },
 { value: number; label: "Médiane" },
 { value: number; label: "Objectif" }
 ];

 selection: {
 enabled: boolean;
 onSelect: (range: [number, number]) => void;
 };
 };

 outliers: {
 high: Client[];
 low: Client[];

 actions: {
 investigate: (client: Client) => void;
 adjust: (client: Client) => void;
 };
 };
 };
 };

 competitiveness: {
 title: "Positionnement concurrentiel";

 marketComparison: {
 sources: ["market_data", "competitors", "benchmarks"];

 position: {
 chart: {
 type: "radar";
 dimensions: [
 "Prix moyen",
 "Flexibilité",
 "Services inclus",
 "Satisfaction",
 "Innovation"
 ];

 series: [
 { name: "Notre offre", data: number[] },
 { name: "Moyenne marché", data: number[] },
 { name: "Leader marché", data: number[] }
 ];
 };

 insights: CompetitiveInsight[];
 recommendations: PositioningRecommendation[];
 };

 priceElasticity: {
 analysis: ElasticityData;

 simulator: {
 currentPrice: number;

 scenarios: Array<{
 priceChange: number;
 volumeImpact: number;
 revenueImpact: number;
 probability: number;
 }>;

 optimal: {
 price: number;
 expectedRevenue: number;
 confidence: number;
 };
 };
 };
 };
 };

 optimization: {
 title: "Opportunités d'optimisation";

 recommendations: Array<{
 id: string;
 type: "price_increase" | "price_decrease" | "restructure" | "migrate";
 priority: "high" | "medium" | "low";

 description: string;
 impact: {
 revenue: number;
 clients: number;
 risk: RiskLevel;
 };

 details: {
 current: any;
 proposed: any;
 rationale: string;
 steps: Step[];
 };

 actions: {
 simulate: () => void;
 implement: () => void;
 schedule: () => void;
 dismiss: () => void;
 };
 }>;

 automation: {
 rules: OptimizationRule[];

 triggers: [
 { event: "margin_below_threshold", action: "alert" },
 { event: "volume_change", action: "reprice" },
 { event: "competitor_move", action: "analyze" }
 ];

 monitoring: {
 active: boolean;
 frequency: "realtime" | "daily" | "weekly";
 notifications: NotificationSettings;
 };
 };
 };
 };

 reports: {
 templates: [
 {
 id: "executive_summary";
 name: "Résumé exécutif";
 frequency: "monthly";
 recipients: string[];
 },
 {
 id: "detailed_analysis";
 name: "Analyse détaillée";
 frequency: "quarterly";
 sections: string[];
 },
 {
 id: "client_review";
 name: "Revue clients";
 frequency: "on_demand";
 filters: any;
 }
 ];

 generation: {
 period: DateRange;
 format: "pdf" | "excel" | "powerpoint";

 customization: {
 logo: boolean;
 branding: BrandingOptions;
 charts: ChartOptions;
 language: "fr" | "en";
 };

 schedule: {
 enabled: boolean;
 frequency: string;
 recipients: Recipient[];
 };
 };
 };
}
```

## État et données

```typescript
interface PricingState {
 // Navigation
 activeTab: string;

 // Grilles tarifaires
 grids: {
 list: PricingGrid[];
 filters: GridFilters;
 selected?: PricingGrid;
 loading: boolean;
 };

 // Tarifs clients
 clientPricing: {
 selectedClient?: Client;
 pricing?: ClientPricing;
 history: PricingHistory[];
 bulkSelection: Client[];
 };

 // Simulation
 simulator: {
 scenario: SimulationScenario;
 results?: SimulationResults;
 running: boolean;
 savedScenarios: SavedScenario[];
 };

 // Analyse
 analysis: {
 metrics: AnalyticsData;
 filters: AnalysisFilters;
 recommendations: Recommendation[];
 reports: Report[];
 };

 // État UI
 ui: {
 modals: {
 gridCreation: boolean;
 clientAssignment: boolean;
 simulation: boolean;
 };
 errors: Record<string, Error>;
 notifications: Notification[];
 };

 // Permissions
 permissions: {
 canCreateGrid: boolean;
 canModifyPricing: boolean;
 canRunSimulations: boolean;
 canViewAnalytics: boolean;
 };
}
```

## API Endpoints

```typescript
// Grilles tarifaires
GET /api/pricing/grids
POST /api/pricing/grids
PUT /api/pricing/grids/:id
DELETE /api/pricing/grids/:id

// Tarifs clients
GET /api/pricing/clients/:clientId
POST /api/pricing/clients/:clientId/assign
PUT /api/pricing/clients/:clientId/customize
GET /api/pricing/clients/:clientId/history

// Actions bulk
POST /api/pricing/bulk/assign
POST /api/pricing/bulk/update

// Simulation
POST /api/pricing/simulate
GET /api/pricing/simulate/:id
POST /api/pricing/simulate/:id/save

// Analyse
GET /api/pricing/analytics
GET /api/pricing/analytics/profitability
GET /api/pricing/analytics/optimization
POST /api/pricing/analytics/report

// Market data
GET /api/pricing/market/comparison
GET /api/pricing/market/elasticity
```

## Exemple d'implémentation

```tsx
export const PricingPage: React.FC = () => {
 const [activeTab, setActiveTab] = useState("grids");
 const { grids, loadGrids } = usePricingGrids();
 const { runSimulation, results } = usePricingSimulator();
 const { permissions } = usePermissions();

 // Real-time updates
 useEffect(() => {
 const subscription = subscribeToPricingUpdates((update) => {
 if (update.type === "grid_updated") {
 loadGrids();
 }
 });

 return () => subscription.unsubscribe();
 }, []);

 const handleGridCreate = async (gridData: GridFormData) => {
 try {
 const grid = await createPricingGrid(gridData);
 showNotification("Grille créée avec succès", "success");
 loadGrids();
 } catch (error) {
 showNotification("Erreur lors de la création", "error");
 }
 };

 const handleSimulation = async (scenario: SimulationScenario) => {
 const results = await runSimulation(scenario);

 // Auto-save interesting scenarios
 if (results.savings > 1000) {
 await saveScenario(scenario, results);
 }
 };

 return (
 <PricingLayout>
 <PricingHeader
 activeTab={activeTab}
 onTabChange={setActiveTab}
 permissions={permissions}
 />

 <TabContent>
 {activeTab === "grids" && (
 <PricingGridsTab
 grids={grids}
 onCreateGrid={handleGridCreate}
 onEditGrid={handleGridEdit}
 />
 )}

 {activeTab === "clients" && (
 <ClientPricingTab
 onAssignGrid={handleAssignGrid}
 onCustomizeRate={handleCustomizeRate}
 />
 )}

 {activeTab === "simulator" && (
 <PricingSimulatorTab
 onSimulate={handleSimulation}
 results={results}
 />
 )}

 {activeTab === "analysis" && (
 <PricingAnalysisTab
 onOptimize={handleOptimization}
 onGenerateReport={handleReportGeneration}
 />
 )}
 </TabContent>
 </PricingLayout>
 );
};
```