# Page Projets - Module Facturation

## Vue d'ensemble

La page Projets permet de gérer l'ensemble des projets de facturation pour l'autoconsommation collective photovoltaïque, de la création à la clôture.

## Structure de la page

### Header Principal
```typescript
interface ProjectsPageHeader {
 title: " Gestion des Projets";
 subtitle: "Gérez vos projets d'autoconsommation collective";

 actions: {
 createButton: {
 label: " Nouveau Projet";
 icon: "add_circle";
 color: "primary";
 onClick: () => void;
 permissions: ["create_project"];
 };

 searchBar: {
 placeholder: "Rechercher un projet...";
 value: string;
 onChange: (value: string) => void;
 suggestions: string[];
 onClear: () => void;
 };

 viewToggle: {
 options: ["grid", "list", "kanban"];
 current: ViewMode;
 onChange: (mode: ViewMode) => void;
 };

 filterButton: {
 label: "Filtres";
 icon: "filter_list";
 badge?: number; // Nombre de filtres actifs
 onClick: () => void;
 };
 };
}
```

### Section Liste des Projets
```typescript
interface ProjectsListSection {
 view: {
 mode: "grid" | "list" | "kanban";

 // Vue Grille
 gridView: {
 columns: 3 | 4 | 5; // Responsive
 gap: number;

 projectCard: {
 id: string;
 nom: string;
 reference: string;
 status: ProjectStatus;
 type: "autoconso_collective" | "vente_surplus";

 header: {
 logo?: string;
 statusBadge: {
 label: string;
 color: StatusColor;
 icon: string;
 };
 favoriteToggle: boolean;
 };

 metrics: {
 participants: {
 total: number;
 producteurs: number;
 consommateurs: number;
 };
 puissance: {
 installee: number; // kWc
 production: number; // MWh/an
 };
 finance: {
 ca_mensuel: number;
 ca_annuel: number;
 marge: number; // %
 };
 };

 timeline: {
 dateCreation: Date;
 dateLancement: Date;
 duree: number; // mois
 progression: number; // %
 };

 quickStats: Array<{
 label: string;
 value: number | string;
 icon: string;
 trend?: "up" | "down" | "stable";
 }>;

 actions: {
 primary: {
 label: "Tableau de bord";
 onClick: () => void;
 };
 secondary: [
 { label: "Participants", icon: "people", onClick: () => void },
 { label: "Factures", icon: "receipt", onClick: () => void },
 { label: "Paramètres", icon: "settings", onClick: () => void }
 ];
 };
 };
 };

 // Vue Liste
 listView: {
 columns: Array<{
 field: string;
 header: string;
 sortable: boolean;
 width?: number;
 render?: (value: any, row: Project) => ReactNode;
 }>;

 expandableRows: {
 enabled: boolean;
 renderExpanded: (project: Project) => ReactNode;
 };

 rowActions: Array<{
 icon: string;
 tooltip: string;
 onClick: (project: Project) => void;
 visible?: (project: Project) => boolean;
 }>;

 bulkActions: {
 enabled: boolean;
 actions: [
 { label: "Exporter", icon: "download", action: (ids: string[]) => void },
 { label: "Archiver", icon: "archive", action: (ids: string[]) => void },
 { label: "Dupliquer", icon: "content_copy", action: (ids: string[]) => void }
 ];
 };
 };

 // Vue Kanban
 kanbanView: {
 columns: Array<{
 id: ProjectStatus;
 title: string;
 color: string;
 itemsCount: number;
 maxItems?: number;
 }>;

 card: {
 compact: boolean;
 showMetrics: boolean;
 draggable: boolean;
 onDragEnd: (projectId: string, newStatus: ProjectStatus) => void;
 };

 swimlanes?: {
 field: "type" | "region" | "gestionnaire";
 enabled: boolean;
 };
 };
 };

 sorting: {
 field: string;
 direction: "asc" | "desc";
 options: Array<{
 value: string;
 label: string;
 }>;
 };

 pagination: {
 enabled: boolean;
 pageSize: number;
 currentPage: number;
 totalItems: number;
 pageSizeOptions: [10, 25, 50, 100];
 };
}
```

### Section Création/Édition Projet
```typescript
interface ProjectFormSection {
 mode: "create" | "edit" | "duplicate";

 steps: [
 {
 id: "basic_info";
 title: "Informations Générales";
 icon: "info";
 fields: {
 nom: {
 type: "text";
 label: "Nom du projet";
 required: true;
 validation: { minLength: 3, maxLength: 100 };
 };
 reference: {
 type: "text";
 label: "Référence interne";
 required: true;
 autoGenerate: boolean;
 pattern: /^PROJ-\d{4}-\d{3}$/;
 };
 type: {
 type: "select";
 label: "Type de projet";
 options: [
 { value: "autoconso_collective", label: "Autoconsommation collective" },
 { value: "vente_surplus", label: "Vente de surplus" }
 ];
 required: true;
 };
 description: {
 type: "textarea";
 label: "Description";
 rows: 4;
 maxLength: 500;
 };
 gestionnaire: {
 type: "select";
 label: "Gestionnaire PMO";
 options: User[];
 required: true;
 searchable: true;
 };
 };
 },
 {
 id: "technical";
 title: "Paramètres Techniques";
 icon: "engineering";
 fields: {
 puissance_installee: {
 type: "number";
 label: "Puissance installée (kWc)";
 required: true;
 min: 0;
 step: 0.1;
 suffix: "kWc";
 };
 production_estimee: {
 type: "number";
 label: "Production estimée (MWh/an)";
 calculated: true;
 formula: "puissance * heures_ensoleillement * rendement";
 };
 localisation: {
 type: "map_selector";
 label: "Localisation";
 required: true;
 mapOptions: {
 center: [lat, lng];
 zoom: 15;
 drawPolygon: true;
 };
 };
 configuration: {
 type: "nested";
 label: "Configuration technique";
 fields: {
 nb_onduleurs: number;
 type_panneaux: string;
 orientation: number; // degrés
 inclinaison: number; // degrés
 };
 };
 };
 },
 {
 id: "commercial";
 title: "Paramètres Commerciaux";
 icon: "attach_money";
 fields: {
 tarif_vente: {
 type: "number";
 label: "Tarif de vente (€/kWh)";
 required: true;
 min: 0;
 step: 0.001;
 prefix: "€";
 };
 frais_gestion: {
 type: "number";
 label: "Frais de gestion mensuels (€)";
 required: true;
 min: 0;
 prefix: "€";
 };
 mode_facturation: {
 type: "radio";
 label: "Mode de facturation";
 options: [
 { value: "mensuel", label: "Mensuel" },
 { value: "bimestriel", label: "Bimestriel" },
 { value: "trimestriel", label: "Trimestriel" }
 ];
 default: "mensuel";
 };
 conditions_paiement: {
 type: "select";
 label: "Conditions de paiement";
 options: [
 { value: "30j", label: "30 jours" },
 { value: "45j", label: "45 jours" },
 { value: "60j", label: "60 jours" }
 ];
 };
 };
 },
 {
 id: "planning";
 title: "Planning";
 icon: "calendar_today";
 fields: {
 date_debut: {
 type: "date";
 label: "Date de début";
 required: true;
 min: "today";
 };
 duree_contrat: {
 type: "number";
 label: "Durée du contrat (années)";
 required: true;
 min: 1;
 max: 30;
 default: 20;
 };
 jalons: {
 type: "timeline";
 label: "Jalons du projet";
 milestones: [
 { label: "Signature contrats", date: Date, status: "completed" },
 { label: "Installation", date: Date, status: "in_progress" },
 { label: "Mise en service", date: Date, status: "pending" },
 { label: "Première facturation", date: Date, status: "pending" }
 ];
 };
 };
 }
 ];

 validation: {
 onChange: boolean;
 onBlur: boolean;
 showErrors: "inline" | "summary";
 };

 actions: {
 save: {
 label: "Enregistrer";
 onClick: (data: ProjectFormData) => void;
 loading: boolean;
 };
 saveAndContinue: {
 label: "Enregistrer et continuer";
 onClick: (data: ProjectFormData) => void;
 };
 cancel: {
 label: "Annuler";
 onClick: () => void;
 confirmIfDirty: boolean;
 };
 };
}
```

### Section Filtres Avancés
```typescript
interface AdvancedFiltersSection {
 visible: boolean;
 position: "sidebar" | "modal" | "inline";

 filters: {
 status: {
 label: "Statut";
 type: "multiselect";
 options: [
 { value: "actif", label: "Actif", color: "success" },
 { value: "pause", label: "En pause", color: "warning" },
 { value: "cloture", label: "Clôturé", color: "default" },
 { value: "preparation", label: "En préparation", color: "info" }
 ];
 value: string[];
 };

 type: {
 label: "Type de projet";
 type: "checkbox";
 options: ProjectType[];
 value: string[];
 };

 dateRange: {
 label: "Période";
 type: "daterange";
 presets: [
 { label: "Ce mois", value: [startOfMonth, endOfMonth] },
 { label: "Ce trimestre", value: [startOfQuarter, endOfQuarter] },
 { label: "Cette année", value: [startOfYear, endOfYear] }
 ];
 value: [Date, Date];
 };

 financial: {
 label: "Critères financiers";
 type: "group";
 expanded: boolean;
 filters: {
 ca_min: { type: "number", label: "CA minimum (€)", min: 0 };
 ca_max: { type: "number", label: "CA maximum (€)", min: 0 };
 marge_min: { type: "number", label: "Marge minimum (%)", min: 0, max: 100 };
 has_impaye: { type: "boolean", label: "Avec impayés" };
 };
 };

 participants: {
 label: "Participants";
 type: "range";
 min: 0;
 max: 1000;
 value: [number, number];
 showHistogram: true;
 };

 tags: {
 label: "Tags";
 type: "tags";
 suggestions: string[];
 value: string[];
 allowCustom: true;
 };
 };

 savedFilters: {
 enabled: boolean;
 list: Array<{
 id: string;
 name: string;
 filters: FilterValues;
 isDefault: boolean;
 }>;
 actions: {
 save: (name: string) => void;
 load: (id: string) => void;
 delete: (id: string) => void;
 setDefault: (id: string) => void;
 };
 };

 actions: {
 apply: () => void;
 reset: () => void;
 close: () => void;
 };
}
```

### Section Statistiques et Analyse
```typescript
interface ProjectStatisticsSection {
 title: " Vue d'ensemble des projets";

 summary: {
 totalProjects: number;
 activeProjects: number;
 totalParticipants: number;
 totalPower: number; // MWc
 totalRevenue: number; // €/mois
 averageMargin: number; // %
 };

 charts: {
 statusDistribution: {
 type: "PieChart";
 data: { status: string; count: number; percentage: number }[];
 options: {
 showLegend: true;
 showValues: true;
 colors: StatusColors;
 };
 };

 monthlyGrowth: {
 type: "LineChart";
 title: "Croissance mensuelle";
 data: {
 months: string[];
 newProjects: number[];
 totalProjects: number[];
 };
 options: {
 showArea: true;
 showPoints: true;
 dual_axis: true;
 };
 };

 revenueByType: {
 type: "BarChart";
 title: "Revenus par type";
 data: {
 types: string[];
 revenue: number[];
 count: number[];
 };
 options: {
 stacked: false;
 showValues: true;
 formatValue: (v: number) => `${v.toFixed(0)}€`;
 };
 };

 geographicDistribution: {
 type: "MapChart";
 title: "Répartition géographique";
 data: {
 regions: GeoJSON;
 values: { [regionId: string]: number };
 };
 options: {
 colorScale: "sequential";
 showTooltip: true;
 enableZoom: true;
 };
 };
 };

 insights: {
 enabled: boolean;
 items: Array<{
 type: "info" | "warning" | "success";
 title: string;
 description: string;
 metric?: { value: number; trend: "up" | "down" };
 action?: { label: string; onClick: () => void };
 }>;
 };
}
```

## État et données

```typescript
interface ProjectsPageState {
 // Liste des projets
 projects: {
 items: Project[];
 totalCount: number;
 loading: boolean;
 error?: Error;
 };

 // Filtres et recherche
 filters: {
 search: string;
 status: string[];
 type: string[];
 dateRange?: [Date, Date];
 financial?: FinancialFilters;
 tags: string[];
 };

 // Affichage
 view: {
 mode: "grid" | "list" | "kanban";
 sorting: { field: string; direction: "asc" | "desc" };
 pagination: { page: number; size: number };
 };

 // Formulaire
 form: {
 visible: boolean;
 mode: "create" | "edit" | "duplicate";
 data?: Partial<Project>;
 errors: ValidationErrors;
 dirty: boolean;
 };

 // Sélection
 selection: {
 ids: string[];
 mode: "single" | "multiple";
 };

 // Statistiques
 statistics: {
 summary: ProjectSummary;
 charts: ChartData;
 insights: Insight[];
 };
}
```

## API Endpoints

```typescript
// Projets
GET /api/billing/projects
Query: { search?, status?, type?, page?, limit?, sort? }

GET /api/billing/projects/:id
GET /api/billing/projects/:id/participants
GET /api/billing/projects/:id/invoices
GET /api/billing/projects/:id/statistics

POST /api/billing/projects
PUT /api/billing/projects/:id
DELETE /api/billing/projects/:id

// Actions
POST /api/billing/projects/:id/activate
POST /api/billing/projects/:id/pause
POST /api/billing/projects/:id/close
POST /api/billing/projects/:id/duplicate

// Export
GET /api/billing/projects/export
Query: { format: "excel" | "csv" | "pdf", ids?: string[] }

// Statistiques
GET /api/billing/projects/statistics
GET /api/billing/projects/insights
```

## Exemple d'implémentation

```tsx
export const ProjectsPage: React.FC = () => {
 const [viewMode, setViewMode] = useState<ViewMode>("grid");
 const [filters, setFilters] = useState<ProjectFilters>({});
 const [showForm, setShowForm] = useState(false);

 const { projects, statistics, loading } = useProjects(filters);

 return (
 <PageLayout>
 <ProjectsPageHeader
 onCreateNew={() => setShowForm(true)}
 onViewModeChange={setViewMode}
 onSearch={(search) => setFilters({...filters, search })}
 />

 <Grid container spacing={3}>
 {/* Statistiques */}
 <Grid item xs={12}>
 <ProjectStatistics data={statistics} />
 </Grid>

 {/* Liste des projets */}
 <Grid item xs={12}>
 {viewMode === "grid" && (
 <ProjectGrid
 projects={projects}
 onProjectClick={handleProjectClick}
 />
 )}
 {viewMode === "list" && (
 <ProjectList
 projects={projects}
 onProjectClick={handleProjectClick}
 />
 )}
 {viewMode === "kanban" && (
 <ProjectKanban
 projects={projects}
 onStatusChange={handleStatusChange}
 />
 )}
 </Grid>
 </Grid>

 {/* Formulaire de création/édition */}
 <ProjectFormDialog
 open={showForm}
 onClose={() => setShowForm(false)}
 onSave={handleSaveProject}
 />

 {/* Filtres avancés */}
 <AdvancedFilters
 filters={filters}
 onChange={setFilters}
 />
 </PageLayout>
 );
};
```