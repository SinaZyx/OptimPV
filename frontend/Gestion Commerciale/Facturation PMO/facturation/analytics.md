# Page Analytics - Module Facturation

## Vue d'ensemble

La page Analytics fournit des analyses approfondies et des statistiques avancées sur l'activité de facturation, permettant d'identifier les tendances, optimiser les performances et prendre des décisions éclairées.

## Structure de la page

### Header Principal
```typescript
interface AnalyticsPageHeader {
 title: " Analytics Facturation";
 subtitle: "Analyses détaillées et insights sur votre activité";

 actions: {
 periodSelector: {
 label: "Période d'analyse";
 type: "advanced";
 value: {
 start: Date;
 end: Date;
 comparison?: {
 enabled: boolean;
 type: "previous_period" | "same_period_last_year" | "custom";
 start?: Date;
 end?: Date;
 };
 };
 presets: [
 { label: "7 derniers jours", value: "7d" },
 { label: "30 derniers jours", value: "30d" },
 { label: "Ce trimestre", value: "quarter" },
 { label: "Cette année", value: "year" },
 { label: "Année glissante", value: "rolling_year" }
 ];
 onChange: (period: PeriodConfig) => void;
 };

 refreshButton: {
 label: "Actualiser";
 icon: "refresh";
 loading: boolean;
 lastUpdate: Date;
 onClick: () => void;
 };

 exportDropdown: {
 label: "Exporter";
 icon: "download";
 options: [
 {
 id: "dashboard_pdf",
 label: "Tableau de bord PDF",
 icon: "picture_as_pdf",
 description: "Export complet avec graphiques"
 },
 {
 id: "raw_data",
 label: "Données brutes Excel",
 icon: "table_chart",
 description: "Toutes les données analysées"
 },
 {
 id: "presentation",
 label: "Présentation PowerPoint",
 icon: "slideshow",
 description: "Slides avec points clés"
 }
 ];
 onExport: (format: string) => void;
 };

 shareButton: {
 label: "Partager";
 icon: "share";
 onClick: () => void;
 generateLink: () => string;
 };
 };
}
```

### Section Métriques Clés avec Comparaison
```typescript
interface KeyMetricsSection {
 title: " Métriques Clés";

 metrics: Array<{
 id: string;
 label: string;
 value: number;
 previousValue?: number;
 format: "number" | "currency" | "percentage" | "duration";

 comparison: {
 enabled: boolean;
 value: number;
 percentage: number;
 trend: "up" | "down" | "stable";
 isPositive: boolean;
 label: string; // ex: "vs période précédente"
 };

 sparkline: {
 data: number[];
 type: "line" | "bar" | "area";
 color: string;
 showPoints: boolean;
 };

 breakdown?: {
 label: string;
 items: Array<{
 label: string;
 value: number;
 percentage: number;
 color: string;
 }>;
 };

 target?: {
 value: number;
 achievement: number; // percentage
 label: string;
 };

 forecast?: {
 value: number;
 confidence: number; // 0-100
 label: string;
 };
 }>;

 layout: {
 columns: 2 | 3 | 4 | 6;
 responsive: boolean;
 cardStyle: "minimal" | "detailed" | "compact";
 };
}
```

### Section Analyses Temporelles
```typescript
interface TemporalAnalysisSection {
 title: " Analyses Temporelles";

 charts: {
 revenueAnalysis: {
 title: "Évolution des Revenus";
 type: "MultiLineChart";

 data: {
 timestamps: Date[];
 series: [
 {
 name: "Revenus facturés";
 data: number[];
 color: "#2196f3";
 type: "line";
 },
 {
 name: "Revenus encaissés";
 data: number[];
 color: "#4caf50";
 type: "line";
 },
 {
 name: "Prévisions";
 data: number[];
 color: "#ff9800";
 type: "dashed";
 forecast: true;
 }
 ];

 annotations: Array<{
 type: "line" | "box" | "point";
 value: any;
 label: string;
 color: string;
 }>;
 };

 controls: {
 granularity: {
 options: ["hour", "day", "week", "month", "quarter"];
 current: string;
 onChange: (value: string) => void;
 };

 smoothing: {
 enabled: boolean;
 type: "moving_average" | "exponential";
 window: number;
 };

 showComparison: boolean;
 showForecast: boolean;
 showAnomalies: boolean;
 };

 insights: Array<{
 type: "trend" | "anomaly" | "pattern" | "forecast";
 severity: "info" | "warning" | "critical";
 message: string;
 data?: any;
 }>;
 };

 seasonality: {
 title: "Saisonnalité";
 type: "HeatmapChart";

 data: {
 months: string[];
 days: number[];
 values: number[][];
 scale: {
 min: number;
 max: number;
 colors: string[];
 };
 };

 patterns: Array<{
 type: "weekly" | "monthly" | "yearly";
 strength: number; // 0-100
 description: string;
 }>;
 };

 cohortAnalysis: {
 title: "Analyse de Cohortes";
 type: "CohortTable";

 data: {
 cohorts: Array<{
 label: string;
 startDate: Date;
 size: number;
 }>;

 periods: string[];

 metrics: {
 retention: number[][];
 revenue: number[][];
 ltv: number[][];
 };
 };

 settings: {
 metric: "retention" | "revenue" | "ltv";
 cohortType: "monthly" | "quarterly" | "custom";
 showPercentages: boolean;
 };
 };
 };
}
```

### Section Analyses par Segment
```typescript
interface SegmentAnalysisSection {
 title: " Analyses par Segment";

 segments: {
 definition: {
 dimensions: [
 "project_type",
 "project_size",
 "geographic_region",
 "customer_type",
 "payment_behavior"
 ];

 customSegments: Array<{
 id: string;
 name: string;
 rules: SegmentRule[];
 color: string;
 }>;
 };

 comparison: {
 title: "Comparaison des Segments";
 type: "RadarChart" | "ParallelCoordinates";

 dimensions: [
 { key: "revenue", label: "Revenus", normalize: true },
 { key: "growth", label: "Croissance", normalize: true },
 { key: "payment_rate", label: "Taux de paiement", normalize: true },
 { key: "satisfaction", label: "Satisfaction", normalize: true },
 { key: "profitability", label: "Rentabilité", normalize: true }
 ];

 segments: Array<{
 id: string;
 name: string;
 values: number[];
 size: number;
 color: string;
 }>;

 insights: {
 bestPerforming: string;
 worstPerforming: string;
 opportunities: string[];
 };
 };

 distribution: {
 title: "Distribution des Revenus";
 type: "TreemapChart";

 data: {
 name: "Total";
 value: number;
 children: Array<{
 name: string;
 value: number;
 percentage: number;
 growth: number;
 children?: any[];
 }>;
 };

 interactions: {
 drillDown: boolean;
 showPath: boolean;
 onSegmentClick: (segment: Segment) => void;
 };
 };

 performance: {
 title: "Performance par Segment";
 type: "BubbleChart";

 axes: {
 x: { metric: "revenue", label: "Revenus (€)", scale: "linear" };
 y: { metric: "growth", label: "Croissance (%)", scale: "linear" };
 size: { metric: "participant_count", label: "Nombre de participants" };
 color: { metric: "payment_rate", label: "Taux de paiement" };
 };

 bubbles: Array<{
 segment: string;
 x: number;
 y: number;
 size: number;
 color: number;
 metadata: any;
 }>;

 quadrants: {
 show: boolean;
 labels: ["Déclin", "Émergent", "Mature", "Star"];
 };
 };
 };
}
```

### Section Analyses Prédictives
```typescript
interface PredictiveAnalyticsSection {
 title: " Analyses Prédictives";

 models: {
 revenueForecast: {
 title: "Prévisions de Revenus";
 type: "ForecastChart";

 data: {
 historical: {
 dates: Date[];
 values: number[];
 };

 forecast: {
 dates: Date[];
 predictions: number[];
 confidence: {
 lower: number[];
 upper: number[];
 level: 0.95;
 };
 };

 model: {
 type: "ARIMA" | "Prophet" | "LSTM";
 accuracy: number;
 mape: number; // Mean Absolute Percentage Error
 parameters: any;
 };
 };

 scenarios: [
 {
 name: "Optimiste";
 multiplier: 1.2;
 color: "#4caf50";
 probability: 0.25;
 },
 {
 name: "Réaliste";
 multiplier: 1.0;
 color: "#2196f3";
 probability: 0.50;
 },
 {
 name: "Pessimiste";
 multiplier: 0.8;
 color: "#f44336";
 probability: 0.25;
 }
 ];

 controls: {
 horizon: { value: 3; unit: "months"; max: 12 };
 showConfidence: boolean;
 showScenarios: boolean;
 adjustSeasonality: boolean;
 };
 };

 churnPrediction: {
 title: "Prédiction d'Attrition";
 type: "RiskMatrix";

 participants: Array<{
 id: string;
 name: string;
 churnProbability: number;
 riskScore: number;
 value: number; // Revenue impact

 factors: {
 paymentDelay: number;
 engagementScore: number;
 satisfactionScore: number;
 contractRemaining: number;
 };

 recommendations: string[];
 }>;

 visualization: {
 type: "ScatterPlot" | "HeatMap";
 axes: {
 x: "churnProbability";
 y: "value";
 };

 segments: [
 { label: "High Risk - High Value", color: "#f44336", action: "urgent" },
 { label: "High Risk - Low Value", color: "#ff9800", action: "monitor" },
 { label: "Low Risk - High Value", color: "#4caf50", action: "retain" },
 { label: "Low Risk - Low Value", color: "#9e9e9e", action: "maintain" }
 ];
 };
 };

 anomalyDetection: {
 title: "Détection d'Anomalies";
 type: "TimelineChart";

 data: {
 timestamps: Date[];
 values: number[];
 anomalies: Array<{
 timestamp: Date;
 value: number;
 severity: "low" | "medium" | "high";
 type: "spike" | "drop" | "pattern";
 explanation: string;
 }>;
 };

 settings: {
 sensitivity: number; // 0-1
 method: "isolation_forest" | "lstm_autoencoder" | "statistical";
 realTime: boolean;
 };

 alerts: {
 enabled: boolean;
 channels: ["email", "sms", "webhook"];
 thresholds: {
 low: { enabled: boolean; action: "log" };
 medium: { enabled: boolean; action: "notify" };
 high: { enabled: boolean; action: "alert" };
 };
 };
 };
 };
}
```

### Section Analyses Comportementales
```typescript
interface BehavioralAnalyticsSection {
 title: " Analyses Comportementales";

 analyses: {
 paymentPatterns: {
 title: "Modèles de Paiement";
 type: "SankeyDiagram";

 data: {
 nodes: Array<{
 id: string;
 label: string;
 color: string;
 }>;

 links: Array<{
 source: string;
 target: string;
 value: number;
 label?: string;
 }>;
 };

 insights: {
 commonPaths: Path[];
 bottlenecks: string[];
 recommendations: string[];
 };
 };

 customerJourney: {
 title: "Parcours Client";
 type: "JourneyMap";

 stages: [
 {
 name: "Adhésion";
 touchpoints: Touchpoint[];
 satisfaction: number;
 dropoffRate: number;
 },
 {
 name: "Première Facture";
 touchpoints: Touchpoint[];
 satisfaction: number;
 dropoffRate: number;
 },
 {
 name: "Paiement Régulier";
 touchpoints: Touchpoint[];
 satisfaction: number;
 dropoffRate: number;
 },
 {
 name: "Fidélisation";
 touchpoints: Touchpoint[];
 satisfaction: number;
 dropoffRate: number;
 }
 ];

 metrics: {
 nps: number;
 csat: number;
 ces: number; // Customer Effort Score
 };
 };

 segmentMigration: {
 title: "Migration entre Segments";
 type: "AlluvialDiagram";

 periods: string[];

 flows: Array<{
 fromSegment: string;
 toSegment: string;
 count: number;
 value: number;
 retention: number;
 }>;

 analysis: {
 upgrades: number;
 downgrades: number;
 churn: number;
 netMovement: number;
 };
 };
 };
}
```

### Section Tableau de Bord Personnalisable
```typescript
interface CustomDashboardSection {
 title: " Tableau de Bord Personnalisé";

 widgets: Array<{
 id: string;
 type: WidgetType;
 title: string;
 position: { x: number; y: number; w: number; h: number };

 config: {
 dataSource: string;
 visualization: string;
 filters: any[];
 refreshInterval?: number;
 };

 actions: {
 fullscreen: boolean;
 export: boolean;
 configure: boolean;
 remove: boolean;
 };
 }>;

 layout: {
 type: "grid" | "freeform";
 columns: 12;
 rowHeight: 60;
 compactType: "vertical" | "horizontal";
 preventCollision: boolean;
 };

 widgetLibrary: {
 categories: [
 {
 name: "Graphiques",
 widgets: ChartWidget[];
 },
 {
 name: "Métriques",
 widgets: MetricWidget[];
 },
 {
 name: "Tableaux",
 widgets: TableWidget[];
 },
 {
 name: "Cartes",
 widgets: MapWidget[];
 }
 ];
 };

 actions: {
 addWidget: (widget: Widget) => void;
 removeWidget: (id: string) => void;
 updateLayout: (layout: Layout[]) => void;
 saveTemplate: (name: string) => void;
 loadTemplate: (id: string) => void;
 shareTemplate: () => string;
 };
}
```

## État et données

```typescript
interface AnalyticsPageState {
 // Configuration
 config: {
 period: {
 start: Date;
 end: Date;
 comparison?: ComparisonPeriod;
 };
 segments: string[];
 filters: AnalyticsFilters;
 };

 // Données
 data: {
 metrics: MetricData[];
 temporal: TemporalData;
 segments: SegmentData;
 predictions: PredictionData;
 behavioral: BehavioralData;
 loading: boolean;
 lastUpdate: Date;
 };

 // Insights
 insights: {
 automated: AutomatedInsight[];
 custom: CustomInsight[];
 recommendations: Recommendation[];
 };

 // Dashboard personnalisé
 customDashboard: {
 widgets: Widget[];
 layout: Layout[];
 templates: Template[];
 };

 // Exports
 exports: {
 scheduled: ScheduledExport[];
 history: ExportHistory[];
 };
}
```

## API Endpoints

```typescript
// Analytics principales
GET /api/billing/analytics/metrics
Query: { period, comparison?, metrics[], segments[] }

GET /api/billing/analytics/temporal
Query: { period, granularity, series[], smoothing? }

GET /api/billing/analytics/segments
Query: { dimensions[], metrics[], limit? }

// Prédictif
GET /api/billing/analytics/forecast
Query: { metric, horizon, model?, scenarios? }

GET /api/billing/analytics/churn-prediction
Query: { threshold?, includeFactors? }

GET /api/billing/analytics/anomalies
Query: { period, sensitivity, method }

// Comportemental
GET /api/billing/analytics/payment-patterns
GET /api/billing/analytics/customer-journey
GET /api/billing/analytics/segment-migration

// Insights
GET /api/billing/analytics/insights
Query: { types[], minConfidence? }

POST /api/billing/analytics/insights/feedback
Body: { insightId, helpful: boolean, comment? }

// Export
POST /api/billing/analytics/export
Body: { format, sections[], period, email? }

// Dashboard personnalisé
GET /api/billing/analytics/dashboard/widgets
POST /api/billing/analytics/dashboard/widgets
PUT /api/billing/analytics/dashboard/layout
```

## Exemple d'implémentation

```tsx
export const AnalyticsPage: React.FC = () => {
 const [period, setPeriod] = useState<PeriodConfig>(defaultPeriod);
 const [activeTab, setActiveTab] = useState("overview");

 const {
 metrics,
 temporal,
 segments,
 predictions,
 insights,
 loading
 } = useAnalytics(period);

 return (
 <PageLayout>
 <AnalyticsPageHeader
 period={period}
 onPeriodChange={setPeriod}
 onExport={handleExport}
 />

 <Tabs value={activeTab} onChange={setActiveTab}>
 <Tab label="Vue d'ensemble" value="overview" />
 <Tab label="Temporel" value="temporal" />
 <Tab label="Segments" value="segments" />
 <Tab label="Prédictif" value="predictive" />
 <Tab label="Comportemental" value="behavioral" />
 <Tab label="Personnalisé" value="custom" />
 </Tabs>

 <TabPanel value={activeTab} index="overview">
 <Grid container spacing={3}>
 <Grid item xs={12}>
 <KeyMetrics data={metrics} comparison={period.comparison} />
 </Grid>
 <Grid item xs={12}>
 <InsightsPanel insights={insights} />
 </Grid>
 </Grid>
 </TabPanel>

 <TabPanel value={activeTab} index="temporal">
 <TemporalAnalysis data={temporal} />
 </TabPanel>

 <TabPanel value={activeTab} index="segments">
 <SegmentAnalysis data={segments} />
 </TabPanel>

 <TabPanel value={activeTab} index="predictive">
 <PredictiveAnalytics data={predictions} />
 </TabPanel>

 <TabPanel value={activeTab} index="behavioral">
 <BehavioralAnalytics data={behavioral} />
 </TabPanel>

 <TabPanel value={activeTab} index="custom">
 <CustomDashboard />
 </TabPanel>
 </PageLayout>
 );
};
```