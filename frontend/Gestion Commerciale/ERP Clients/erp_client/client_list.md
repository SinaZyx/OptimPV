# Page Liste des Clients - Module ERP Client

## Vue d'ensemble

La page Liste des Clients est l'interface centrale de gestion des clients avec trois modes d'affichage (Tableau, Cartes, Kanban) et des fonctionnalités avancées de recherche et filtrage.

## Structure de la page

### Header Principal
```typescript
interface ClientListHeader {
 title: " Gestion des Clients";

 actions: {
 viewModeSelector: {
 options: [
 { value: "table", label: " Tableau", icon: "table_rows" },
 { value: "cards", label: " Cartes", icon: "grid_view" },
 { value: "kanban", label: " Kanban", icon: "view_kanban" }
 ];
 value: ViewMode;
 onChange: (mode: ViewMode) => void;
 };

 newClientButton: {
 label: " Nouveau client";
 variant: "primary";
 onClick: () => void;
 shortcut: "Ctrl+N";
 };

 quickActionsMenu: {
 label: " Actions";
 items: [
 { id: "import", label: " Importer Excel", icon: "upload_file" },
 { id: "export", label: " Exporter", icon: "download" },
 { id: "sync", label: " Synchroniser API", icon: "sync" },
 { id: "bulk_edit", label: " Édition en masse", icon: "edit_note" }
 ];
 onAction: (actionId: string) => void;
 };
 };
}
```

### Section Filtres et Recherche
```typescript
interface SearchFiltersSection {
 searchBar: {
 placeholder: " Recherche par nom, code client, email, téléphone...";
 value: string;
 onChange: (value: string) => void;
 onClear: () => void;
 suggestions: string[]; // Suggestions basées sur l'historique
 debounceMs: 300;
 };

 quickFilters: {
 row1: [
 {
 id: "type";
 label: "Type";
 type: "select";
 value: string;
 options: [
 { value: "all", label: "Tous" },
 { value: "producteur", label: "Producteur", count: number },
 { value: "consommateur", label: "Consommateur", count: number },
 { value: "prosumer", label: "Prosumer", count: number }
 ];
 },
 {
 id: "status";
 label: "Statut";
 type: "select";
 value: string;
 options: [
 { value: "all", label: "Tous" },
 { value: "active", label: "Actifs", color: "success" },
 { value: "inactive", label: "Inactifs", color: "warning" },
 { value: "suspended", label: "Suspendus", color: "error" }
 ];
 },
 {
 id: "zone";
 label: "Zone géographique";
 type: "select";
 value: string;
 options: string[]; // Chargées dynamiquement
 searchable: true;
 },
 {
 id: "period";
 label: "Période";
 type: "select";
 value: string;
 options: [
 "Toutes",
 "Aujourd'hui",
 "Cette semaine",
 "Ce mois",
 "3 derniers mois",
 "Cette année"
 ];
 }
 ];
 };

 advancedFilters: {
 isExpanded: boolean;
 toggle: () => void;

 filters: {
 locationFilters: {
 title: " Localisation";
 hasGPS: boolean;
 radius: { center: [number, number]; distance: number };
 department: string[];
 city: string[];
 };

 businessFilters: {
 title: " Activité";
 hasPricing: boolean;
 hasProduction: boolean;
 revenueRange: [number, number];
 consumptionRange: [number, number];
 };

 tagsFilters: {
 title: " Tags";
 selectedTags: string[];
 availableTags: ["VIP", "À risque", "Nouveau", "Grand compte", "PME", "Résidentiel"];
 operator: "AND" | "OR";
 };
 };

 onApply: (filters: AdvancedFilters) => void;
 onReset: () => void;
 onSaveAsPreset: (name: string) => void;
 };
}
```

### Section Statistiques Rapides
```typescript
interface QuickStatsBar {
 metrics: [
 {
 label: "Total Clients";
 value: number;
 delta: { value: number; label: "ce mois"; trend: "up" | "down" };
 onClick: () => void;
 },
 {
 label: "Clients Actifs";
 value: number;
 percentage: number; // % du total
 color: "success";
 },
 {
 label: "Producteurs";
 value: number;
 sublabel: "Incluant prosumers";
 icon: "solar_power";
 },
 {
 label: "Géocodés";
 value: number;
 percentage: number;
 action: { label: "Géocoder", onClick: () => void };
 },
 {
 label: "CA Total";
 value: number;
 format: "currency";
 evolution: { value: number; period: "YoY" };
 },
 {
 label: "Nouveaux";
 value: number;
 period: "30 jours";
 sparkline: number[]; // Mini graphique
 }
 ];

 layout: "horizontal-scroll-mobile";
 refreshInterval: 30000; // Auto-refresh 30s
}
```

### Mode Tableau
```typescript
interface TableViewMode {
 columns: [
 {
 id: "select";
 type: "checkbox";
 width: 40;
 fixed: true;
 },
 {
 id: "code_client";
 label: "Code";
 sortable: true;
 width: 100;
 render: (value: string) => <CodeBadge value={value} />;
 },
 {
 id: "nom";
 label: "Nom";
 sortable: true;
 searchable: true;
 width: 200;
 render: (client: Client) => (
 <ClientNameCell
 name={client.nom}
 avatar={client.avatar}
 tags={client.tags}
 />
 );
 },
 {
 id: "type_client";
 label: "Type";
 sortable: true;
 filterable: true;
 width: 120;
 render: (type: string) => <TypeBadge type={type} />;
 },
 {
 id: "zone";
 label: "Zone";
 sortable: true;
 width: 150;
 render: (zone: string) => <ZoneChip zone={zone} />;
 },
 {
 id: "status";
 label: "Statut";
 sortable: true;
 width: 100;
 render: (status: string) => <StatusIndicator status={status} />;
 },
 {
 id: "last_activity";
 label: "Dernière activité";
 sortable: true;
 width: 150;
 render: (date: Date) => <RelativeTime date={date} />;
 },
 {
 id: "actions";
 label: "Actions";
 width: 150;
 fixed: "right";
 render: (client: Client) => (
 <ActionButtons
 actions={[
 { icon: "visibility", tooltip: "Voir", onClick: () => {} },
 { icon: "edit", tooltip: "Éditer", onClick: () => {} },
 { icon: "euro", tooltip: "Tarification", onClick: () => {} },
 { icon: "map", tooltip: "Localiser", onClick: () => {} },
 { icon: "more_vert", tooltip: "Plus", onClick: () => {} }
 ]}
 />
 );
 }
 ];

 features: {
 sorting: {
 multiColumn: true;
 defaultSort: { column: "last_activity", direction: "desc" };
 };

 selection: {
 mode: "multiple";
 showCheckboxes: true;
 onSelectionChange: (selected: string[]) => void;
 };

 pagination: {
 pageSize: 25;
 pageSizeOptions: [10, 25, 50, 100];
 showTotal: true;
 };

 rowActions: {
 onRowClick: (client: Client) => void;
 onRowDoubleClick: (client: Client) => void;
 contextMenu: MenuItem[];
 };

 export: {
 formats: ["excel", "csv", "pdf"];
 customColumns: boolean;
 includeFilters: boolean;
 };
 };

 bulkActions: {
 visible: boolean; // when selection > 0
 actions: [
 { id: "edit", label: "Éditer", icon: "edit" },
 { id: "delete", label: "Supprimer", icon: "delete", danger: true },
 { id: "export", label: "Exporter", icon: "download" },
 { id: "assign", label: "Assigner", icon: "person_add" },
 { id: "tag", label: "Tagger", icon: "label" }
 ];
 onAction: (actionId: string, selectedIds: string[]) => void;
 };
}
```

### Mode Cartes
```typescript
interface CardsViewMode {
 layout: {
 type: "grid";
 columns: { desktop: 4; tablet: 2; mobile: 1 };
 gap: 16;
 animation: "fadeIn";
 };

 cardTemplate: {
 header: {
 avatar: {
 src: string | null;
 fallback: string; // Initiales
 color: string; // Basé sur le type
 };
 title: string; // Nom client
 subtitle: string; // Code client
 badge: { text: string; color: string }; // Statut
 };

 body: {
 fields: [
 { label: "Type", value: string, icon: "category" },
 { label: "Zone", value: string, icon: "location_on" },
 { label: "Contact", value: string, icon: "phone" },
 { label: "CA annuel", value: string, icon: "euro", format: "currency" }
 ];

 tags: string[];

 metrics: {
 production?: { value: number; unit: "kWh/an" };
 consommation?: { value: number; unit: "kWh/an" };
 };
 };

 footer: {
 lastActivity: Date;
 actions: [
 { icon: "visibility", tooltip: "Détails" },
 { icon: "edit", tooltip: "Éditer" },
 { icon: "euro", tooltip: "Tarifs" },
 { icon: "delete", tooltip: "Supprimer", danger: true }
 ];
 };
 };

 interactions: {
 onClick: (client: Client) => void;
 onHover: { showQuickInfo: boolean };
 onActionClick: (action: string, client: Client) => void;
 selectable: boolean;
 };

 sorting: {
 options: ["nom", "date_creation", "ca_annuel", "last_activity"];
 current: string;
 direction: "asc" | "desc";
 };
}
```

### Mode Kanban
```typescript
interface KanbanViewMode {
 columns: [
 {
 id: "prospects";
 title: " Prospects";
 color: "#e3f2fd";
 filter: (client: Client) => client.status === "prospect";
 limit?: number;
 collapsed: boolean;
 },
 {
 id: "active";
 title: " Actifs";
 color: "#e8f5e9";
 filter: (client: Client) => client.status === "active";
 },
 {
 id: "onboarding";
 title: " En cours";
 color: "#fff3e0";
 filter: (client: Client) => client.status === "onboarding";
 },
 {
 id: "suspended";
 title: " Suspendus";
 color: "#fce4ec";
 filter: (client: Client) => client.status === "suspended";
 },
 {
 id: "archived";
 title: " Archivés";
 color: "#f5f5f5";
 filter: (client: Client) => client.status === "archived";
 collapsed: true;
 }
 ];

 cardTemplate: {
 compact: true;
 showAvatar: true;
 fields: ["nom", "type", "zone", "derniere_activite"];
 quickActions: ["view", "edit"];
 };

 features: {
 dragDrop: {
 enabled: true;
 onDrop: (clientId: string, newStatus: string) => void;
 validation: (client: Client, targetColumn: string) => boolean;
 };

 search: {
 perColumn: true;
 global: true;
 };

 addCard: {
 enabled: true;
 quickAdd: boolean; // Formulaire rapide inline
 };

 columnActions: {
 collapse: boolean;
 reorder: boolean;
 colorCustomization: boolean;
 };
 };
}
```

## État et données

```typescript
interface ClientListState {
 // Données
 clients: {
 data: Client[];
 total: number;
 loading: boolean;
 error: Error | null;
 };

 // Filtres actifs
 filters: {
 search: string;
 type: string;
 status: string;
 zone: string;
 period: string;
 advanced: AdvancedFilters;
 };

 // UI State
 ui: {
 viewMode: "table" | "cards" | "kanban";
 selectedIds: string[];
 sorting: SortConfig;
 pagination: PaginationConfig;
 expandedRows: string[];
 };

 // Stats
 stats: {
 total: number;
 active: number;
 byType: Record<string, number>;
 byZone: Record<string, number>;
 revenue: MonthlyRevenue[];
 };
}
```

## API Endpoints

```typescript
// Liste et recherche
GET /api/clients
Query: {
 search?: string;
 type?: string;
 status?: string;
 zone?: string;
 page: number;
 limit: number;
 sort: string;
 order: "asc" | "desc";
}

// Actions bulk
POST /api/clients/bulk
Body: {
 action: string;
 clientIds: string[];
 data?: any;
}

// Import/Export
POST /api/clients/import
GET /api/clients/export

// Statistiques
GET /api/clients/stats
```

## Exemple d'implémentation

```tsx
export const ClientListPage: React.FC = () => {
 const [viewMode, setViewMode] = useState<ViewMode>("table");
 const [filters, setFilters] = useState<Filters>(defaultFilters);
 const { clients, stats, loading } = useClients(filters);

 return (
 <PageLayout>
 <ClientListHeader
 viewMode={viewMode}
 onViewModeChange={setViewMode}
 onNewClient={() => navigate("/clients/new")}
 />

 <SearchFiltersSection
 filters={filters}
 onChange={setFilters}
 />

 <QuickStatsBar stats={stats} />

 <ViewContainer>
 {viewMode === "table" && (
 <TableView
 clients={clients}
 onSort={handleSort}
 onSelect={handleSelect}
 />
 )}

 {viewMode === "cards" && (
 <CardsView
 clients={clients}
 onCardClick={handleCardClick}
 />
 )}

 {viewMode === "kanban" && (
 <KanbanView
 clients={clients}
 onStatusChange={handleStatusChange}
 />
 )}
 </ViewContainer>
 </PageLayout>
 );
};
```