# Page Dashboard - Module Facturation

## Vue d'ensemble

Le Dashboard Facturation offre une vue exécutive complète de l'activité de facturation pour les projets d'autoconsommation collective photovoltaïque.

## Structure de la page

### Header Principal
```typescript
interface BillingDashboardHeader {
 title: " Tableau de Bord Facturation";
 subtitle: "Vue d'ensemble de l'activité de facturation PMO";

 actions: {
 refreshButton: {
 label: " Actualiser";
 onClick: () => void;
 lastUpdate: Date;
 autoRefresh: { enabled: boolean; interval: 60000 };
 };

 periodSelector: {
 label: "Période";
 value: Period;
 options: [
 "Aujourd'hui",
 "Cette semaine",
 "Ce mois",
 "Ce trimestre",
 "Cette année",
 "Personnalisé"
 ];
 onChange: (period: Period) => void;
 };

 exportMenu: {
 label: " Exporter";
 options: [
 { id: "pdf", label: "Rapport PDF", icon: "picture_as_pdf" },
 { id: "excel", label: "Excel détaillé", icon: "table_chart" },
 { id: "csv", label: "Données CSV", icon: "csv" }
 ];
 onExport: (format: string) => void;
 };
 };
}
```

### Section KPIs Principaux
```typescript
interface MainKPIsSection {
 title: " Indicateurs Clés";
 layout: "grid-6-responsive"; // 6 cartes sur desktop

 kpis: [
 {
 id: "total_projects";
 label: "Projets Total";
 value: number;
 icon: "";
 color: "primary";
 trend: { value: number; isPositive: boolean };
 sparkline: number[]; // 7 derniers jours
 onClick: () => void; // Navigation vers projets
 },
 {
 id: "active_projects";
 label: "Projets Actifs";
 value: number;
 icon: "";
 color: "success";
 percentage: number; // % du total
 subLabel: "En production";
 },
 {
 id: "total_participants";
 label: "Participants";
 value: number;
 icon: "";
 color: "info";
 breakdown: {
 producteurs: number;
 consommateurs: number;
 };
 },
 {
 id: "invoices_generated";
 label: "Factures Générées";
 value: number;
 icon: "";
 color: "warning";
 period: "Ce mois";
 comparison: { previous: number; change: number };
 },
 {
 id: "total_revenue";
 label: "Revenus Totaux";
 value: number;
 format: "currency";
 icon: "";
 color: "success";
 breakdown: {
 facturé: number;
 encaissé: number;
 enAttente: number;
 };
 },
 {
 id: "collection_rate";
 label: "Taux de Recouvrement";
 value: number;
 format: "percentage";
 icon: "";
 color: value => value > 90? "success": value > 70? "warning": "error";
 target: 95;
 gauge: true; // Affichage en gauge
 }
 ];

 animations: {
 countUp: true;
 duration: 1000;
 easing: "easeOutQuart";
 };
}
```

### Section Graphiques d'Analyse
```typescript
interface AnalyticsChartsSection {
 title: " Analyses";

 charts: {
 revenueEvolution: {
 title: "Évolution des Revenus";
 type: "AreaChart";
 data: {
 labels: string[]; // Mois
 series: [
 { name: "Facturé", data: number[], color: "#2196f3" },
 { name: "Encaissé", data: number[], color: "#4caf50" },
 { name: "En attente", data: number[], color: "#ff9800" }
 ];
 };
 options: {
 stacked: false;
 showGrid: true;
 enableZoom: true;
 showLegend: true;
 annotations: [
 { type: "line", value: number, label: "Objectif" }
 ];
 };
 timeControls: ["1M", "3M", "6M", "1Y", "ALL"];
 };

 projectDistribution: {
 title: "Répartition par Projet";
 type: "DonutChart";
 data: {
 labels: string[]; // Noms des projets
 values: number[]; // Revenus par projet
 colors: string[]; // Couleurs automatiques
 };
 options: {
 showPercentages: true;
 showValues: true;
 interactive: true;
 onClick: (projectId: string) => void;
 };
 centerMetric: {
 label: "Total";
 value: number;
 format: "currency";
 };
 };

 paymentStatus: {
 title: "Statut des Paiements";
 type: "StackedBarChart";
 data: {
 categories: string[]; // Mois
 series: [
 { name: "Payé à temps", data: number[], color: "#4caf50" },
 { name: "Retard < 30j", data: number[], color: "#ff9800" },
 { name: "Retard > 30j", data: number[], color: "#f44336" }
 ];
 };
 options: {
 horizontal: false;
 showValues: true;
 percentage: true;
 };
 };

 participantActivity: {
 title: "Activité Participants";
 type: "HeatmapCalendar";
 data: {
 dates: Date[];
 values: number[]; // Nombre de factures
 maxValue: number;
 };
 options: {
 colorScale: ["#eee", "#4caf50"];
 showTooltips: true;
 cellSize: 15;
 };
 };
 };

 layout: {
 grid: [
 { chart: "revenueEvolution", cols: 8, rows: 4 },
 { chart: "projectDistribution", cols: 4, rows: 4 },
 { chart: "paymentStatus", cols: 6, rows: 3 },
 { chart: "participantActivity", cols: 6, rows: 3 }
 ];
 responsive: true;
 };
}
```

### Section Projets Actifs
```typescript
interface ActiveProjectsSection {
 title: " Projets Actifs";
 viewToggle: {
 options: ["cards", "table"];
 current: string;
 onChange: (view: string) => void;
 };

 projectCards: Array<{
 id: string;
 nom: string;
 type: "autoconso_collective" | "vente_surplus";
 status: "active" | "pause" | "cloture";

 metrics: {
 participants: { total: number; actifs: number };
 facturation: {
 montantMensuel: number;
 dernièreFacture: Date;
 prochaine: Date;
 };
 recouvrement: {
 taux: number;
 enRetard: number;
 montantRetard: number;
 };
 };

 alerts: Array<{
 type: "warning" | "error" | "info";
 message: string;
 action?: () => void;
 }>;

 quickActions: [
 { label: "Voir détails", icon: "visibility" },
 { label: "Générer factures", icon: "receipt" },
 { label: "Rapport", icon: "assessment" }
 ];

 progressBars: {
 facturation: { current: number; total: number };
 paiements: { current: number; total: number };
 };
 }>;

 sorting: {
 options: ["nom", "montant", "participants", "taux_recouvrement"];
 current: string;
 direction: "asc" | "desc";
 };

 filters: {
 status: string[];
 hasAlerts: boolean;
 minParticipants: number;
 };
}
```

### Section Alertes et Actions
```typescript
interface AlertsActionsSection {
 alerts: {
 title: " Alertes";
 items: Array<{
 id: string;
 severity: "high" | "medium" | "low";
 type: "payment_delay" | "invoice_error" | "participant_issue" | "system";
 title: string;
 description: string;
 timestamp: Date;
 project?: { id: string; name: string };
 participant?: { id: string; name: string };
 actions: Array<{
 label: string;
 action: () => void;
 primary?: boolean;
 }>;
 }>;

 filters: {
 severity: string[];
 type: string[];
 resolved: boolean;
 };

 bulkActions: {
 markAsRead: () => void;
 markAsResolved: () => void;
 export: () => void;
 };
 };

 quickActions: {
 title: " Actions Rapides";
 grid: [
 {
 label: "Générer Factures Mensuelles";
 icon: "receipt_long";
 color: "primary";
 description: "Pour tous les projets actifs";
 onClick: () => void;
 badge?: number; // Nombre de projets concernés
 },
 {
 label: "Envoyer Rappels";
 icon: "mail";
 color: "warning";
 description: "Paiements en retard";
 onClick: () => void;
 badge?: number; // Nombre de rappels
 },
 {
 label: "Rapport Mensuel";
 icon: "assessment";
 color: "info";
 description: "Générer rapport complet";
 onClick: () => void;
 },
 {
 label: "Import Paiements";
 icon: "account_balance";
 color: "success";
 description: "Depuis fichier bancaire";
 onClick: () => void;
 }
 ];
 };
}
```

### Section Activité Récente
```typescript
interface RecentActivitySection {
 title: " Activité Récente";

 timeline: {
 items: Array<{
 id: string;
 type: "invoice" | "payment" | "participant" | "alert";
 icon: string;
 color: string;
 title: string;
 description: string;
 timestamp: Date;
 user?: { name: string; avatar?: string };
 metadata?: Record<string, any>;
 actions?: Array<{
 label: string;
 onClick: () => void;
 }>;
 }>;

 groupBy: "day" | "hour" | "none";

 filters: {
 types: string[];
 projects: string[];
 dateRange: [Date, Date];
 };

 loadMore: {
 hasMore: boolean;
 loading: boolean;
 onLoadMore: () => void;
 };
 };

 stats: {
 todayCount: number;
 weekCount: number;
 trending: "up" | "down" | "stable";
 };
}
```

## État et données

```typescript
interface BillingDashboardState {
 // Métriques principales
 kpis: {
 totalProjects: number;
 activeProjects: number;
 participants: ParticipantStats;
 invoices: InvoiceStats;
 revenue: RevenueStats;
 collectionRate: number;
 };

 // Données graphiques
 analytics: {
 revenueData: TimeSeriesData;
 projectDistribution: DistributionData;
 paymentStatus: PaymentStatusData;
 activityHeatmap: HeatmapData;
 };

 // Projets actifs
 projects: {
 list: Project[];
 stats: ProjectStats;
 alerts: ProjectAlert[];
 };

 // Alertes système
 alerts: {
 items: Alert[];
 unreadCount: number;
 criticalCount: number;
 };

 // Activité
 activity: {
 timeline: ActivityItem[];
 stats: ActivityStats;
 hasMore: boolean;
 };

 // Configuration
 config: {
 period: Period;
 autoRefresh: boolean;
 filters: DashboardFilters;
 };
}
```

## API Endpoints

```typescript
// Dashboard principal
GET /api/billing/dashboard
Query: { period, projectIds?, refresh? }

// KPIs temps réel
GET /api/billing/kpis
WebSocket: /ws/billing/kpis (mises à jour temps réel)

// Analytics
GET /api/billing/analytics/revenue
GET /api/billing/analytics/distribution
GET /api/billing/analytics/payment-status

// Activité
GET /api/billing/activity
Query: { limit, offset, types?, projects? }

// Actions
POST /api/billing/actions/generate-invoices
POST /api/billing/actions/send-reminders
POST /api/billing/actions/generate-report
```

## Exemple d'implémentation

```tsx
export const BillingDashboard: React.FC = () => {
 const [period, setPeriod] = useState<Period>("Ce mois");
 const { kpis, analytics, projects, alerts, activity } = useBillingDashboard(period);

 return (
 <DashboardLayout>
 <BillingDashboardHeader
 period={period}
 onPeriodChange={setPeriod}
 onExport={handleExport}
 />

 <Grid container spacing={3}>
 {/* KPIs */}
 <Grid item xs={12}>
 <KPICards data={kpis} animated />
 </Grid>

 {/* Graphiques */}
 <Grid item xs={12} lg={8}>
 <RevenueChart data={analytics.revenue} />
 </Grid>
 <Grid item xs={12} lg={4}>
 <ProjectDistribution data={analytics.distribution} />
 </Grid>

 {/* Projets actifs */}
 <Grid item xs={12}>
 <ActiveProjects
 projects={projects}
 viewMode="cards"
 />
 </Grid>

 {/* Alertes et actions */}
 <Grid item xs={12} md={6}>
 <AlertsPanel alerts={alerts} />
 </Grid>
 <Grid item xs={12} md={6}>
 <QuickActions />
 </Grid>

 {/* Activité récente */}
 <Grid item xs={12}>
 <ActivityTimeline items={activity} />
 </Grid>
 </Grid>
 </DashboardLayout>
 );
};
```