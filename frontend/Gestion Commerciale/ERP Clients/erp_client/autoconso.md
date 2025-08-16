# Gestion Autoconsommation Collective - Module ERP Client

## Vue d'ensemble

La page d'autoconsommation collective permet de gérer les communautés énergétiques, optimiser la répartition de l'énergie entre producteurs et consommateurs, suivre les flux en temps réel et gérer la facturation avec des clés de répartition dynamiques.

## Structure de la page

### Header Principal
```typescript
interface AutoconsoHeader {
 title: " Autoconsommation Collective";

 navigation: {
 breadcrumb: [
 { label: "ERP Client", path: "/erp" },
 { label: "Autoconsommation", path: "/erp/autoconso" },
 { label: communityName, path: `/erp/autoconso/${communityId}` }
 ];

 communitySelector: {
 current: Community | null;
 list: Community[];
 onChange: (community: Community) => void;

 quickInfo: {
 members: number;
 production: number; // kW installés
 status: "active" | "planning" | "suspended";
 };
 };
 };

 actions: {
 newCommunityButton: {
 label: "Nouvelle communauté";
 icon: "group_add";
 variant: "primary";
 onClick: () => void;
 };

 quickActions: {
 items: [
 { id: "simulate", label: "Simuler", icon: "calculate" },
 { id: "report", label: "Rapport", icon: "assessment" },
 { id: "export", label: "Exporter", icon: "download" },
 { id: "settings", label: "Paramètres", icon: "settings" }
 ];
 onAction: (actionId: string) => void;
 };

 viewToggle: {
 options: ["dashboard", "members", "flows", "billing"];
 value: string;
 onChange: (view: string) => void;
 };
 };
}
```

### Vue Dashboard
```typescript
interface DashboardView {
 realTimeMetrics: {
 updateInterval: 5000; // ms

 cards: [
 {
 id: "production";
 title: "Production actuelle";
 value: number;
 unit: "kW";
 icon: "solar_power";
 color: "success";

 gauge: {
 max: number; // Capacité installée
 segments: [
 { threshold: 80, color: "success" },
 { threshold: 50, color: "warning" },
 { threshold: 0, color: "error" }
 ];
 };

 trend: {
 data: number[]; // 24h
 type: "sparkline";
 };
 },
 {
 id: "consumption";
 title: "Consommation";
 value: number;
 unit: "kW";
 icon: "electric_bolt";
 color: "primary";

 breakdown: {
 internal: number; // Autoconsommé
 grid: number; // Depuis réseau
 percentage: number; // Taux autoconso
 };
 },
 {
 id: "balance";
 title: "Balance énergétique";
 value: number;
 unit: "kW";
 icon: "balance";
 color: string; // Dynamique selon surplus/déficit

 flow: {
 type: "sankey_mini";
 from: ["production", "grid"];
 to: ["consumption", "injection"];
 };
 },
 {
 id: "savings";
 title: "Économies";
 value: number;
 unit: "€";
 icon: "savings";
 color: "info";

 period: {
 current: "today";
 options: ["today", "week", "month", "year"];
 comparison: number; // vs période précédente
 };
 }
 ];
 };

 energyFlow: {
 title: "Flux énergétiques";

 visualization: {
 type: "sankey" | "chord" | "network";

 sankeyDiagram: {
 nodes: Array<{
 id: string;
 label: string;
 type: "producer" | "consumer" | "grid" | "battery";
 value: number;
 color: string;
 }>;

 links: Array<{
 source: string;
 target: string;
 value: number;
 type: "production" | "consumption" | "injection" | "storage";
 }>;

 options: {
 animated: boolean;
 showValues: boolean;
 interactive: boolean;
 timeRange: "realtime" | "hour" | "day";
 };
 };

 controls: {
 zoom: boolean;
 filter: {
 minFlow: number;
 types: string[];
 };
 export: ["png", "svg"];
 };
 };
 };

 performanceIndicators: {
 layout: "grid";

 kpis: [
 {
 id: "self_consumption_rate";
 label: "Taux d'autoconsommation";
 value: number;
 format: "percentage";
 target: number;

 chart: {
 type: "radial";
 color: string; // Selon performance
 showTarget: boolean;
 };

 details: {
 formula: string;
 breakdown: TimeBreakdown[];
 };
 },
 {
 id: "self_sufficiency_rate";
 label: "Taux d'autosuffisance";
 value: number;
 format: "percentage";

 evolution: {
 period: "month";
 data: TimeSeriesData[];
 showTrend: boolean;
 };
 },
 {
 id: "peak_reduction";
 label: "Réduction des pointes";
 value: number;
 format: "percentage";

 comparison: {
 before: number;
 after: number;
 savings: number;
 };
 },
 {
 id: "co2_avoided";
 label: "CO₂ évité";
 value: number;
 unit: "kg";

 equivalent: {
 trees: number;
 cars: number;
 display: "tooltip";
 };
 }
 ];
 };

 alerts: {
 position: "top";
 dismissible: true;

 items: Array<{
 id: string;
 type: "info" | "warning" | "error" | "success";
 title: string;
 message: string;
 timestamp: Date;

 action?: {
 label: string;
 onClick: () => void;
 };

 details?: {
 affected: string[];
 impact: string;
 resolution: string;
 };
 }>;
 };
}
```

### Vue Membres
```typescript
interface MembersView {
 statistics: {
 summary: {
 total: number;
 producers: number;
 consumers: number;
 prosumers: number;

 capacity: {
 production: number; // kWc total
 storage: number; // kWh batteries
 };

 growth: {
 newThisMonth: number;
 trend: "up" | "down" | "stable";
 };
 };
 };

 membersList: {
 filters: {
 search: string;
 type: ("producer" | "consumer" | "prosumer")[];
 status: ("active" | "pending" | "suspended")[];
 zone: string[];
 };

 view: {
 mode: "table" | "cards" | "map";
 groupBy: "type" | "zone" | "status" | null;
 };

 table: {
 columns: [
 {
 id: "member";
 label: "Membre";
 render: (member: Member) => MemberCell;
 sortable: true;
 },
 {
 id: "type";
 label: "Type";
 render: (type: MemberType) => TypeBadge;
 filterable: true;
 },
 {
 id: "capacity";
 label: "Capacité";
 render: (member: Member) => CapacityInfo;
 sortable: true;
 },
 {
 id: "share";
 label: "Part";
 render: (share: number) => ShareDisplay;
 editable: true;
 },
 {
 id: "balance";
 label: "Balance";
 render: (balance: EnergyBalance) => BalanceChart;
 },
 {
 id: "status";
 label: "Statut";
 render: (status: MemberStatus) => StatusBadge;
 },
 {
 id: "actions";
 label: "Actions";
 render: (member: Member) => ActionButtons;
 }
 ];

 rowExpansion: {
 enabled: boolean;
 content: (member: Member) => MemberDetails;
 };

 bulkActions: {
 selection: string[];
 actions: [
 { id: "update_shares", label: "Modifier parts" },
 { id: "suspend", label: "Suspendre" },
 { id: "export", label: "Exporter" }
 ];
 };
 };

 cards: {
 layout: "grid";

 card: {
 header: {
 avatar: string;
 name: string;
 type: MemberType;
 badge: MemberBadge;
 };

 body: {
 metrics: [
 { label: "Production", value: number, unit: "kWh/mois" },
 { label: "Consommation", value: number, unit: "kWh/mois" },
 { label: "Part", value: number, unit: "%" },
 { label: "Économies", value: number, unit: "€/mois" }
 ];

 chart: {
 type: "mini_area";
 data: DailyProduction[];
 height: 60;
 };
 };

 footer: {
 lastSync: Date;
 actions: MemberAction[];
 };
 };
 };

 map: {
 center: [number, number];
 zoom: number;

 markers: {
 clustering: boolean;

 types: {
 producer: { icon: "solar_panel", color: "#4CAF50" };
 consumer: { icon: "home", color: "#2196F3" };
 prosumer: { icon: "sync", color: "#FF9800" };
 };

 popup: {
 content: (member: Member) => PopupContent;
 actions: PopupAction[];
 };
 };

 overlays: {
 productionZones: boolean;
 gridConnection: boolean;
 range: { radius: number; unit: "km" };
 };
 };
 };

 memberManagement: {
 addMember: {
 button: {
 label: "Ajouter membre";
 icon: "person_add";
 onClick: () => void;
 };

 modal: {
 steps: [
 {
 id: "search";
 title: "Rechercher client";
 content: ClientSearch;
 },
 {
 id: "configure";
 title: "Configurer";
 content: MemberConfiguration;
 },
 {
 id: "validate";
 title: "Valider";
 content: ValidationSummary;
 }
 ];

 validation: {
 checkEligibility: boolean;
 verifyDocuments: boolean;
 calculateShares: boolean;
 };
 };
 };

 editMember: {
 form: {
 shares: {
 type: "static" | "dynamic";
 value: number;

 calculation: {
 method: "fixed" | "production" | "consumption" | "custom";
 parameters: ShareParameters;
 preview: SharePreview;
 };
 };

 billing: {
 tariff: string;
 customRates: CustomRate[];
 paymentMethod: PaymentMethod;
 };

 notifications: {
 alerts: NotificationPreference[];
 reports: ReportFrequency;
 channel: ("email" | "sms" | "app")[];
 };
 };
 };
 };
}
```

### Vue Flux Énergétiques
```typescript
interface EnergyFlowsView {
 timeControls: {
 mode: "realtime" | "historical";

 realtime: {
 refreshRate: number; // secondes
 pause: boolean;
 buffer: number; // minutes de données
 };

 historical: {
 range: DateRange;
 granularity: "minute" | "hour" | "day" | "month";
 comparison: {
 enabled: boolean;
 period: DateRange;
 };
 };

 presets: [
 { label: "Temps réel", value: "realtime" },
 { label: "Aujourd'hui", value: "today" },
 { label: "Hier", value: "yesterday" },
 { label: "Cette semaine", value: "week" },
 { label: "Ce mois", value: "month" }
 ];
 };

 flowVisualization: {
 mainChart: {
 type: "stacked_area" | "flow_diagram" | "heatmap";

 stackedArea: {
 series: Array<{
 name: string;
 data: TimeSeriesData[];
 color: string;
 type: "production" | "consumption";
 stackOrder: number;
 }>;

 axes: {
 x: { type: "time"; format: string };
 y: { title: "Puissance (kW)"; min: number; max: number };
 };

 interactions: {
 zoom: boolean;
 pan: boolean;
 tooltip: {
 shared: boolean;
 formatter: (data: any) => string;
 };

 selection: {
 enabled: boolean;
 onSelect: (range: TimeRange) => void;
 };
 };

 annotations: Array<{
 type: "line" | "box" | "text";
 value: any;
 label: string;
 color: string;
 }>;
 };

 flowDiagram: {
 layout: "hierarchical" | "circular" | "force";

 nodes: FlowNode[];
 edges: FlowEdge[];

 animation: {
 particleFlow: boolean;
 speed: number;
 density: number;
 };

 filters: {
 minFlow: number;
 memberTypes: string[];
 timeWindow: number;
 };
 };
 };

 detailPanels: {
 layout: "bottom" | "side";

 panels: [
 {
 id: "member_details";
 title: "Détails membre";

 content: {
 selectedMember: Member | null;

 metrics: {
 production: ProductionMetrics;
 consumption: ConsumptionMetrics;
 balance: BalanceMetrics;
 };

 charts: {
 daily: DailyPattern;
 weekly: WeeklyPattern;
 seasonal: SeasonalPattern;
 };
 };
 },
 {
 id: "flow_analysis";
 title: "Analyse des flux";

 content: {
 statistics: FlowStatistics;
 patterns: FlowPattern[];
 anomalies: Anomaly[];

 optimization: {
 suggestions: Suggestion[];
 potential: SavingsPotential;
 simulate: () => void;
 };
 };
 }
 ];
 };
 };

 sharingKeys: {
 current: {
 method: "static" | "dynamic" | "hybrid";

 keys: Array<{
 memberId: string;
 production: number; // %
 consumption: number; // %
 lastUpdate: Date;
 }>;

 visualization: {
 type: "pie" | "treemap" | "bar";
 interactive: boolean;
 };
 };

 configuration: {
 methods: [
 {
 id: "static";
 label: "Statique";
 description: "Clés fixes définies manuellement";
 icon: "lock";
 },
 {
 id: "production_based";
 label: "Basé sur production";
 description: "Proportionnel à la production installée";
 icon: "solar_power";
 },
 {
 id: "consumption_based";
 label: "Basé sur consommation";
 description: "Proportionnel à la consommation";
 icon: "electric_bolt";
 },
 {
 id: "dynamic";
 label: "Dynamique";
 description: "Ajusté en temps réel";
 icon: "sync";
 },
 {
 id: "custom";
 label: "Personnalisé";
 description: "Formule personnalisée";
 icon: "functions";
 }
 ];

 parameters: {
 updateFrequency: "realtime" | "hourly" | "daily" | "monthly";

 constraints: Array<{
 type: "min" | "max" | "equal";
 member: string;
 value: number;
 }>;

 priorities: Array<{
 member: string;
 priority: number;
 conditions: Condition[];
 }>;
 };

 simulation: {
 period: DateRange;
 scenario: Scenario;

 results: {
 distribution: Distribution[];
 fairness: FairnessMetrics;
 efficiency: EfficiencyMetrics;
 };

 comparison: {
 methods: string[];
 metrics: ComparisonMetrics;
 recommendation: string;
 };
 };
 };
 };
}
```

### Vue Facturation
```typescript
interface BillingView {
 overview: {
 period: {
 current: BillingPeriod;
 selector: PeriodSelector;
 };

 summary: {
 cards: [
 {
 title: "Montant total";
 value: number;
 format: "currency";
 breakdown: {
 energy: number;
 services: number;
 taxes: number;
 };
 },
 {
 title: "Économies réalisées";
 value: number;
 format: "currency";
 comparison: {
 withoutACC: number;
 percentage: number;
 };
 },
 {
 title: "Factures émises";
 value: number;
 status: {
 paid: number;
 pending: number;
 overdue: number;
 };
 },
 {
 title: "Taux recouvrement";
 value: number;
 format: "percentage";
 trend: Trend;
 }
 ];
 };
 };

 billingProcess: {
 steps: {
 current: BillingStep;

 workflow: [
 {
 id: "data_collection";
 label: "Collecte données";
 status: "completed" | "in_progress" | "pending";

 tasks: [
 { name: "Import compteurs", status: TaskStatus },
 { name: "Validation données", status: TaskStatus },
 { name: "Calcul répartitions", status: TaskStatus }
 ];
 },
 {
 id: "calculation";
 label: "Calculs";
 status: StepStatus;

 details: {
 membersProcessed: number;
 totalMembers: number;
 errors: CalculationError[];
 };
 },
 {
 id: "validation";
 label: "Validation";
 status: StepStatus;

 checks: [
 { name: "Cohérence totaux", status: CheckStatus },
 { name: "Limites tarifaires", status: CheckStatus },
 { name: "Règles métier", status: CheckStatus }
 ];
 },
 {
 id: "generation";
 label: "Génération";
 status: StepStatus;

 options: {
 format: "pdf" | "electronic";
 template: string;
 language: string;
 };
 },
 {
 id: "sending";
 label: "Envoi";
 status: StepStatus;

 channels: {
 email: number;
 portal: number;
 postal: number;
 };
 }
 ];

 actions: {
 next: () => void;
 previous: () => void;
 cancel: () => void;
 retry: () => void;
 };
 };

 configuration: {
 templates: BillingTemplate[];

 rules: {
 rounding: RoundingRule;
 minimumCharge: number;
 lateFees: LateFeeRule;

 specialCases: Array<{
 condition: string;
 action: string;
 priority: number;
 }>;
 };

 automation: {
 enabled: boolean;
 schedule: CronExpression;
 notifications: AutomationNotification[];
 };
 };
 };

 invoiceManagement: {
 list: {
 filters: {
 status: InvoiceStatus[];
 member: string;
 dateRange: DateRange;
 amountRange: [number, number];
 };

 table: {
 columns: InvoiceColumn[];
 sorting: SortConfig;
 pagination: PaginationConfig;

 rowActions: [
 { icon: "visibility", action: "view" },
 { icon: "download", action: "download" },
 { icon: "send", action: "resend" },
 { icon: "edit", action: "adjust" }
 ];

 bulkActions: {
 download: boolean;
 export: boolean;
 markAsPaid: boolean;
 sendReminder: boolean;
 };
 };
 };

 detail: {
 invoice: Invoice | null;

 sections: {
 header: InvoiceHeader;

 consumption: {
 total: number;
 fromCommunity: number;
 fromGrid: number;

 hourlyBreakdown: HourlyData[];
 graphical: boolean;
 };

 production: {
 total: number;
 selfConsumed: number;
 shared: number;
 injected: number;
 };

 charges: {
 lines: ChargeLine[];

 subtotals: {
 energy: number;
 services: number;
 taxes: TaxBreakdown[];
 total: number;
 };
 };

 payment: {
 method: PaymentMethod;
 dueDate: Date;

 history: Payment[];

 actions: {
 pay: () => void;
 schedule: () => void;
 dispute: () => void;
 };
 };
 };

 actions: {
 download: { formats: ["pdf", "xml", "csv"] };
 print: () => void;
 email: () => void;
 adjust: { enabled: boolean; permissions: string[] };
 };
 };
 };

 analytics: {
 revenue: {
 chart: {
 type: "line";
 series: RevenueSeries[];
 granularity: "day" | "month" | "year";
 };

 breakdown: {
 byMember: RevenueByMember[];
 byType: RevenueByType[];
 byService: RevenueByService[];
 };
 };

 collection: {
 metrics: {
 onTime: number;
 late: number;
 uncollected: number;
 averageDays: number;
 };

 aging: {
 buckets: AgingBucket[];
 chart: "bar" | "waterfall";
 };

 actions: {
 reminders: ReminderCampaign;
 collections: CollectionStrategy;
 };
 };

 profitability: {
 byMember: MemberProfitability[];

 costs: {
 operational: number;
 administrative: number;
 financial: number;
 };

 margins: {
 gross: number;
 operating: number;
 net: number;
 };
 };
 };
}
```

## État et données

```typescript
interface AutoconsoState {
 // Communauté active
 community: {
 current: Community | null;
 list: Community[];
 loading: boolean;
 };

 // Vue active
 view: {
 current: "dashboard" | "members" | "flows" | "billing";
 params: ViewParams;
 };

 // Données temps réel
 realtime: {
 production: RealtimeData;
 consumption: RealtimeData;
 flows: FlowData[];
 lastUpdate: Date;
 connected: boolean;
 };

 // Membres
 members: {
 list: Member[];
 selected: Member | null;
 filters: MemberFilters;
 stats: MemberStats;
 };

 // Facturation
 billing: {
 period: BillingPeriod;
 invoices: Invoice[];
 process: BillingProcess;
 stats: BillingStats;
 };

 // Configuration
 config: {
 sharingKeys: SharingKeyConfig;
 billingRules: BillingRules;
 alerts: AlertConfig;
 };

 // UI
 ui: {
 modals: Record<string, boolean>;
 notifications: Notification[];
 errors: Error[];
 };
}
```

## API Endpoints

```typescript
// Communautés
GET /api/autoconso/communities
POST /api/autoconso/communities
PUT /api/autoconso/communities/:id
DELETE /api/autoconso/communities/:id

// Membres
GET /api/autoconso/communities/:id/members
POST /api/autoconso/communities/:id/members
PUT /api/autoconso/members/:id
DELETE /api/autoconso/members/:id

// Données temps réel
WS /api/autoconso/realtime/:communityId
GET /api/autoconso/flows/:communityId
Query: {
 start: Date;
 end: Date;
 granularity: string;
}

// Clés de répartition
GET /api/autoconso/sharing-keys/:communityId
PUT /api/autoconso/sharing-keys/:communityId
POST /api/autoconso/sharing-keys/simulate

// Facturation
POST /api/autoconso/billing/process
GET /api/autoconso/billing/invoices
POST /api/autoconso/billing/invoices/generate
GET /api/autoconso/billing/analytics

// Optimisation
POST /api/autoconso/optimize
GET /api/autoconso/recommendations/:communityId
```

## Exemple d'implémentation

```tsx
export const AutoconsommationPage: React.FC = () => {
 const { communityId } = useParams();
 const [view, setView] = useState("dashboard");
 const { community, members, realtime } = useAutoconso(communityId);

 // Connexion WebSocket pour temps réel
 useEffect(() => {
 const ws = connectRealtimeData(communityId);

 ws.on("production", updateProduction);
 ws.on("consumption", updateConsumption);
 ws.on("flows", updateFlows);

 return () => ws.close();
 }, [communityId]);

 // Calcul automatique des clés de répartition
 useEffect(() => {
 if (community?.sharingMethod === "dynamic") {
 const interval = setInterval(() => {
 recalculateSharingKeys();
 }, 60000); // Toutes les minutes

 return () => clearInterval(interval);
 }
 }, [community]);

 const handleMemberAdd = async (clientId: string, config: MemberConfig) => {
 try {
 await addMemberToCommunity(communityId, clientId, config);
 showNotification("Membre ajouté avec succès", "success");
 refreshMembers();
 } catch (error) {
 showNotification("Erreur lors de l'ajout", "error");
 }
 };

 const handleBillingProcess = async () => {
 const process = await startBillingProcess(communityId, {
 period: getCurrentPeriod(),
 autoSend: true
 });

 // Suivre le processus
 trackBillingProcess(process.id);
 };

 return (
 <AutoconsoLayout>
 <AutoconsoHeader
 community={community}
 view={view}
 onViewChange={setView}
 onCommunityChange={handleCommunityChange}
 />

 {view === "dashboard" && (
 <DashboardView
 realtime={realtime}
 community={community}
 onAlert={handleAlert}
 />
 )}

 {view === "members" && (
 <MembersView
 members={members}
 onAddMember={handleMemberAdd}
 onEditMember={handleMemberEdit}
 />
 )}

 {view === "flows" && (
 <EnergyFlowsView
 flows={realtime.flows}
 members={members}
 onOptimize={handleOptimization}
 />
 )}

 {view === "billing" && (
 <BillingView
 period={getCurrentPeriod()}
 onProcess={handleBillingProcess}
 onInvoiceAction={handleInvoiceAction}
 />
 )}
 </AutoconsoLayout>
 );
};
```