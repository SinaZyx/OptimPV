# Dashboard Commercial - Module ERP Client

## Vue d'ensemble

Le Dashboard Commercial est l'interface principale de pilotage commercial avec des KPIs temps réel, des graphiques interactifs et des alertes intelligentes pour optimiser la performance commerciale.

## Structure de la page

### Header Principal
```typescript
interface DashboardHeader {
 title: " Dashboard Commercial";
 subtitle: "Vue d'ensemble de l'activité commerciale";

 controls: {
 periodSelector: {
 value: Period;
 options: [
 { value: "today", label: "Aujourd'hui" },
 { value: "week", label: "Cette semaine" },
 { value: "month", label: "Ce mois" },
 { value: "quarter", label: "Ce trimestre" },
 { value: "year", label: "Cette année" },
 { value: "custom", label: "Personnalisé" }
 ];
 onChange: (period: Period) => void;
 customDateRange?: { start: Date; end: Date };
 };

 refreshButton: {
 label: "Actualiser";
 icon: "refresh";
 loading: boolean;
 onClick: () => void;
 autoRefresh: {
 enabled: boolean;
 interval: number; // en secondes
 };
 };

 exportButton: {
 label: "Exporter";
 icon: "download";
 formats: ["PDF", "Excel", "PowerPoint"];
 onExport: (format: string) => void;
 };

 viewModeToggle: {
 options: [
 { value: "overview", label: "Vue d'ensemble", icon: "dashboard" },
 { value: "detailed", label: "Vue détaillée", icon: "analytics" },
 { value: "comparison", label: "Comparaison", icon: "compare_arrows" }
 ];
 value: ViewMode;
 onChange: (mode: ViewMode) => void;
 };
 };
}
```

### Section KPIs Principaux
```typescript
interface MainKPIsSection {
 layout: "grid"; // 4 colonnes desktop, 2 tablet, 1 mobile

 kpis: [
 {
 id: "revenue";
 title: "Chiffre d'affaires";
 value: number;
 format: "currency";
 icon: "euro_symbol";
 color: "primary";

 metrics: {
 current: number;
 previous: number;
 target: number;
 evolution: {
 value: number;
 percentage: number;
 trend: "up" | "down" | "stable";
 };
 };

 sparkline: {
 data: number[];
 type: "line";
 color: string;
 showPoints: boolean;
 };

 details: {
 breakdown: [
 { label: "Producteurs", value: number, percentage: number },
 { label: "Consommateurs", value: number, percentage: number },
 { label: "Services", value: number, percentage: number }
 ];
 };

 actions: {
 viewDetails: () => void;
 exportData: () => void;
 };
 },
 {
 id: "new_clients";
 title: "Nouveaux clients";
 value: number;
 format: "number";
 icon: "person_add";
 color: "success";

 metrics: {
 current: number;
 target: number;
 completionRate: number;
 previousPeriod: number;
 };

 chart: {
 type: "bar";
 data: DailyNewClients[];
 showTrend: boolean;
 };

 segments: [
 { label: "Producteurs", value: number, icon: "solar_power" },
 { label: "Consommateurs", value: number, icon: "electric_bolt" },
 { label: "Prosumers", value: number, icon: "sync_alt" }
 ];
 },
 {
 id: "conversion_rate";
 title: "Taux de conversion";
 value: number;
 format: "percentage";
 icon: "trending_up";
 color: "info";

 funnel: {
 stages: [
 { name: "Prospects", value: number },
 { name: "Qualifiés", value: number },
 { name: "Propositions", value: number },
 { name: "Signés", value: number }
 ];
 showPercentages: boolean;
 animated: boolean;
 };

 comparison: {
 industry: number;
 lastYear: number;
 objective: number;
 };
 },
 {
 id: "active_clients";
 title: "Clients actifs";
 value: number;
 format: "number";
 icon: "group";
 color: "warning";

 gauge: {
 max: number;
 segments: [
 { min: 0, max: 33, color: "error", label: "Faible" },
 { min: 33, max: 66, color: "warning", label: "Moyen" },
 { min: 66, max: 100, color: "success", label: "Élevé" }
 ];
 showNeedle: boolean;
 };

 activity: {
 daily: number;
 weekly: number;
 monthly: number;
 trends: ActivityTrend[];
 };
 }
 ];

 features: {
 hover: {
 showTooltip: boolean;
 expandedInfo: boolean;
 };
 click: {
 drillDown: boolean;
 showModal: boolean;
 };
 customization: {
 reorder: boolean;
 hide: boolean;
 resize: boolean;
 };
 };
}
```

### Section Graphiques Analytiques
```typescript
interface AnalyticsChartsSection {
 layout: {
 type: "masonry";
 columns: { desktop: 2; tablet: 1; mobile: 1 };
 gap: 16;
 };

 charts: [
 {
 id: "revenue_evolution";
 title: "Évolution du CA";
 type: "area";
 size: "large"; // Occupe 2 colonnes

 data: {
 series: [
 {
 name: "CA Réel";
 data: TimeSeriesData[];
 color: "#2196F3";
 },
 {
 name: "CA Prévisionnel";
 data: TimeSeriesData[];
 color: "#4CAF50";
 dashStyle: "dash";
 },
 {
 name: "Objectif";
 data: TimeSeriesData[];
 color: "#FF9800";
 type: "line";
 }
 ];
 };

 options: {
 xAxis: { type: "datetime"; format: "DD/MM" };
 yAxis: { title: "Montant (€)"; format: "currency" };
 legend: { position: "top" };
 zoom: { enabled: true; type: "x" };
 annotations: Annotation[];
 };

 interactions: {
 onPointClick: (point: DataPoint) => void;
 onRangeSelect: (range: DateRange) => void;
 onLegendClick: (series: string) => void;
 };
 },
 {
 id: "client_distribution";
 title: "Répartition clients";
 type: "donut";
 size: "medium";

 data: {
 categories: [
 { name: "Producteurs", value: number, color: "#4CAF50" },
 { name: "Consommateurs", value: number, color: "#2196F3" },
 { name: "Prosumers", value: number, color: "#FF9800" },
 { name: "Inactifs", value: number, color: "#9E9E9E" }
 ];
 total: number;
 };

 options: {
 centerText: { primary: "Total", secondary: number };
 labels: { show: true; format: "percentage" };
 legend: { position: "right"; interactive: true };
 animation: { duration: 1000; type: "fadeIn" };
 };
 },
 {
 id: "geographic_heatmap";
 title: "Carte de densité";
 type: "heatmap";
 size: "medium";

 mapData: {
 center: [number, number];
 zoom: number;
 clusters: ClusterData[];
 heatmapLayer: {
 intensity: number;
 radius: number;
 gradient: ColorGradient;
 };
 };

 controls: {
 layerToggle: ["clients", "revenue", "activity"];
 zoomControls: boolean;
 fullscreen: boolean;
 };
 },
 {
 id: "performance_radar";
 title: "Performance commerciale";
 type: "radar";
 size: "medium";

 data: {
 categories: [
 "Acquisition",
 "Conversion",
 "Rétention",
 "Satisfaction",
 "Croissance",
 "Rentabilité"
 ];
 series: [
 {
 name: "Actuel";
 data: number[];
 color: "#2196F3";
 },
 {
 name: "Objectif";
 data: number[];
 color: "#4CAF50";
 fillOpacity: 0.2;
 }
 ];
 };

 scale: { min: 0; max: 100 };
 },
 {
 id: "pipeline_funnel";
 title: "Pipeline commercial";
 type: "funnel";
 size: "medium";

 stages: [
 {
 name: "Leads";
 value: number;
 conversion: number;
 duration: number; // jours moyens
 color: "#E3F2FD";
 },
 {
 name: "Prospects qualifiés";
 value: number;
 conversion: number;
 duration: number;
 color: "#BBDEFB";
 },
 {
 name: "Propositions";
 value: number;
 conversion: number;
 duration: number;
 color: "#90CAF9";
 },
 {
 name: "Négociations";
 value: number;
 conversion: number;
 duration: number;
 color: "#64B5F6";
 },
 {
 name: "Contrats signés";
 value: number;
 conversion: 100;
 duration: number;
 color: "#2196F3";
 }
 ];

 metrics: {
 totalValue: number;
 averageDealSize: number;
 velocity: number; // jours moyens total
 };
 }
 ];

 features: {
 export: {
 individual: boolean;
 combined: boolean;
 formats: ["PNG", "SVG", "PDF"];
 };

 sharing: {
 enabled: boolean;
 channels: ["email", "slack", "teams"];
 };

 customization: {
 themes: ["light", "dark", "corporate"];
 colorSchemes: ColorScheme[];
 };
 };
}
```

### Section Tableaux de Bord Détaillés
```typescript
interface DetailedDashboards {
 tabs: [
 {
 id: "commercial_activity";
 label: "Activité commerciale";
 icon: "trending_up";

 content: {
 topPerformers: {
 title: "Top performers";
 period: "Ce mois";

 rankings: [
 {
 category: "Meilleurs vendeurs";
 data: SalesPersonRanking[];
 metric: "revenue";
 showProgress: boolean;
 },
 {
 category: "Clients les plus actifs";
 data: ClientActivity[];
 metric: "transactions";
 showTrend: boolean;
 },
 {
 category: "Produits stars";
 data: ProductPerformance[];
 metric: "sales_volume";
 showGrowth: boolean;
 }
 ];
 };

 activityFeed: {
 title: "Activité récente";
 filters: ["all", "deals", "clients", "tasks"];

 items: ActivityItem[];

 features: {
 realTime: boolean;
 notifications: boolean;
 grouping: "time" | "type" | "user";
 };
 };
 };
 },
 {
 id: "financial_metrics";
 label: "Métriques financières";
 icon: "account_balance";

 content: {
 revenueAnalysis: {
 breakdown: {
 byType: RevenueByType[];
 byRegion: RevenueByRegion[];
 byProduct: RevenueByProduct[];
 bySalesperson: RevenueBySalesperson[];
 };

 trends: {
 monthly: MonthlyTrend[];
 quarterly: QuarterlyTrend[];
 yearly: YearlyTrend[];
 };

 forecasting: {
 nextMonth: ForecastData;
 nextQuarter: ForecastData;
 accuracy: number;
 confidence: number;
 };
 };

 profitability: {
 margins: {
 gross: number;
 operating: number;
 net: number;
 };

 costAnalysis: {
 acquisition: number;
 retention: number;
 service: number;
 };

 roi: {
 marketing: number;
 sales: number;
 overall: number;
 };
 };
 };
 },
 {
 id: "team_performance";
 label: "Performance équipe";
 icon: "groups";

 content: {
 teamMetrics: {
 overview: TeamOverview;

 individual: {
 members: TeamMember[];
 comparison: ComparisonMatrix;
 leaderboard: Leaderboard;
 };

 goals: {
 team: Goal[];
 individual: IndividualGoals[];
 progress: ProgressTracking;
 };
 };

 productivity: {
 metrics: ProductivityMetrics;
 efficiency: EfficiencyScore;
 workload: WorkloadDistribution;
 };
 };
 }
 ];
}
```

### Section Alertes et Actions
```typescript
interface AlertsActionsSection {
 position: "bottom" | "side";

 alerts: {
 title: " Alertes";

 items: [
 {
 id: string;
 type: "warning" | "error" | "info" | "success";
 title: string;
 message: string;
 timestamp: Date;

 trigger: {
 metric: string;
 condition: "above" | "below" | "equals";
 threshold: number;
 };

 actions: [
 { label: "Voir détails", onClick: () => void },
 { label: "Ignorer", onClick: () => void },
 { label: "Configurer", onClick: () => void }
 ];

 autoResolve: {
 enabled: boolean;
 condition: string;
 };
 }
 ];

 filters: {
 severity: string[];
 category: string[];
 timeRange: string;
 };

 settings: {
 notifications: {
 email: boolean;
 push: boolean;
 inApp: boolean;
 };

 rules: AlertRule[];
 };
 };

 quickActions: {
 title: " Actions rapides";

 actions: [
 {
 id: "create_report";
 label: "Générer rapport";
 icon: "description";
 color: "primary";
 onClick: () => void;
 },
 {
 id: "schedule_meeting";
 label: "Planifier réunion";
 icon: "event";
 color: "secondary";
 onClick: () => void;
 },
 {
 id: "send_campaign";
 label: "Lancer campagne";
 icon: "campaign";
 color: "success";
 onClick: () => void;
 },
 {
 id: "analyze_segment";
 label: "Analyser segment";
 icon: "analytics";
 color: "info";
 onClick: () => void;
 }
 ];
 };
}
```

## État et données

```typescript
interface DashboardCommercialState {
 // Configuration
 config: {
 period: Period;
 viewMode: "overview" | "detailed" | "comparison";
 autoRefresh: boolean;
 refreshInterval: number;
 };

 // Données KPIs
 kpis: {
 revenue: KPIData;
 newClients: KPIData;
 conversionRate: KPIData;
 activeClients: KPIData;
 customKPIs: CustomKPI[];
 };

 // Données graphiques
 charts: {
 revenue: ChartData;
 distribution: ChartData;
 geographic: MapData;
 performance: RadarData;
 pipeline: FunnelData;
 };

 // Données détaillées
 detailed: {
 topPerformers: PerformerData[];
 activityFeed: ActivityItem[];
 financials: FinancialData;
 teamMetrics: TeamData;
 };

 // Alertes
 alerts: {
 active: Alert[];
 history: Alert[];
 rules: AlertRule[];
 };

 // UI State
 ui: {
 loading: Record<string, boolean>;
 errors: Record<string, Error>;
 expandedSections: string[];
 selectedFilters: FilterState;
 };
}
```

## API Endpoints

```typescript
// KPIs temps réel
GET /api/dashboard/kpis
Query: {
 period: string;
 metrics: string[];
 compare?: boolean;
}

// Données graphiques
GET /api/dashboard/charts/:chartId
Query: {
 period: string;
 granularity: "hour" | "day" | "week" | "month";
 filters?: Record<string, any>;
}

// Alertes
GET /api/dashboard/alerts
POST /api/dashboard/alerts/acknowledge/:alertId
PUT /api/dashboard/alerts/rules

// Export dashboard
POST /api/dashboard/export
Body: {
 format: "pdf" | "excel" | "powerpoint";
 sections: string[];
 period: Period;
}

// WebSocket pour temps réel
WS /api/dashboard/realtime
```

## Exemple d'implémentation

```tsx
export const DashboardCommercial: React.FC = () => {
 const [period, setPeriod] = useState<Period>("month");
 const [viewMode, setViewMode] = useState<ViewMode>("overview");
 const { kpis, charts, alerts, loading } = useDashboard(period);

 useEffect(() => {
 const ws = connectDashboardWebSocket();
 ws.on("kpi:update", handleKPIUpdate);
 ws.on("alert:new", handleNewAlert);

 return () => ws.close();
 }, []);

 return (
 <DashboardLayout>
 <DashboardHeader
 period={period}
 onPeriodChange={setPeriod}
 viewMode={viewMode}
 onViewModeChange={setViewMode}
 />

 <MainKPIsSection
 kpis={kpis}
 loading={loading.kpis}
 onKPIClick={handleKPIClick}
 />

 <AnalyticsChartsSection
 charts={charts}
 loading={loading.charts}
 onChartInteraction={handleChartInteraction}
 />

 {viewMode === "detailed" && (
 <DetailedDashboards
 data={detailedData}
 onTabChange={handleTabChange}
 />
 )}

 <AlertsActionsSection
 alerts={alerts}
 onAlertAction={handleAlertAction}
 onQuickAction={handleQuickAction}
 />
 </DashboardLayout>
 );
};
```