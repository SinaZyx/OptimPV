# Carte des Clients - Module ERP Client

## Vue d'ensemble

La carte des clients offre une visualisation géographique interactive avec clustering intelligent, analyses spatiales avancées, outils de prospection territoriale et intégration avec les données cadastrales et énergétiques.

## Structure de la page

### Header et Contrôles
```typescript
interface CartographyHeader {
 title: " Carte des Clients";

 controls: {
 searchBox: {
 placeholder: "Rechercher un lieu, client, adresse...";
 value: string;
 onChange: (value: string) => void;

 suggestions: {
 clients: Client[];
 addresses: Address[];
 places: Place[];
 };

 onSelect: (item: SearchResult) => void;

 filters: {
 searchIn: ["clients", "addresses", "cities", "poi"];
 radius: number; // km autour du point
 };
 };

 viewControls: {
 mapStyle: {
 options: [
 { value: "streets", label: "Plan", icon: "map" },
 { value: "satellite", label: "Satellite", icon: "satellite" },
 { value: "hybrid", label: "Hybride", icon: "layers" },
 { value: "terrain", label: "Relief", icon: "terrain" }
 ];
 value: string;
 onChange: (style: string) => void;
 };

 layerToggle: {
 button: {
 icon: "layers";
 label: "Couches";
 badge: number; // Nombre de couches actives
 };

 menu: {
 groups: [
 {
 title: "Clients";
 layers: [
 { id: "all_clients", label: "Tous les clients", checked: true },
 { id: "producers", label: "Producteurs", color: "#4CAF50" },
 { id: "consumers", label: "Consommateurs", color: "#2196F3" },
 { id: "prospects", label: "Prospects", color: "#FF9800" }
 ];
 },
 {
 title: "Données";
 layers: [
 { id: "heatmap", label: "Densité", type: "heatmap" },
 { id: "coverage", label: "Zones de couverture", type: "polygon" },
 { id: "grid_connection", label: "Raccordement réseau", type: "line" },
 { id: "solar_potential", label: "Potentiel solaire", type: "raster" }
 ];
 },
 {
 title: "Analyse";
 layers: [
 { id: "clusters", label: "Clusters", type: "cluster" },
 { id: "communities", label: "Communautés ACC", type: "polygon" },
 { id: "competition", label: "Concurrence", type: "marker" },
 { id: "opportunities", label: "Opportunités", type: "highlight" }
 ];
 }
 ];

 onLayerToggle: (layerId: string, visible: boolean) => void;
 onGroupToggle: (groupId: string, visible: boolean) => void;
 };
 };

 toolsMenu: {
 items: [
 { id: "measure", label: "Mesurer", icon: "straighten" },
 { id: "draw", label: "Dessiner", icon: "draw" },
 { id: "analyze", label: "Analyser zone", icon: "analytics" },
 { id: "export", label: "Exporter", icon: "download" },
 { id: "print", label: "Imprimer", icon: "print" }
 ];
 onToolSelect: (toolId: string) => void;
 };
 };

 quickStats: {
 visible: boolean;
 position: "top-right";

 stats: [
 { label: "Clients visibles", value: number, icon: "visibility" },
 { label: "Zone affichée", value: string, icon: "crop_free" },
 { label: "Densité moyenne", value: number, icon: "grain" }
 ];
 };
 };
}
```

### Carte Interactive
```typescript
interface InteractiveMap {
 container: {
 id: "map-container";
 height: "calc(100vh - 200px)";

 controls: {
 zoom: {
 position: "bottom-right";
 showLevel: boolean;
 };

 compass: {
 position: "top-right";
 showHeading: boolean;
 };

 scale: {
 position: "bottom-left";
 metric: boolean;
 imperial: boolean;
 };

 fullscreen: {
 position: "top-right";
 enabled: boolean;
 };

 geolocate: {
 position: "top-right";
 trackUser: boolean;
 showAccuracy: boolean;
 };
 };
 };

 mapConfig: {
 initialView: {
 center: [number, number]; // [lng, lat]
 zoom: number;
 bearing: number;
 pitch: number;
 };

 bounds: {
 france: [[number, number], [number, number]];
 maxBounds: boolean;
 padding: number;
 };

 interactions: {
 dragPan: boolean;
 dragRotate: boolean;
 scrollZoom: boolean;
 boxZoom: boolean;
 doubleClickZoom: boolean;
 touchZoomRotate: boolean;
 };
 };

 markers: {
 clustering: {
 enabled: boolean;

 config: {
 radius: number; // pixels
 maxZoom: number;
 minPoints: number;

 styles: {
 small: { size: 40, color: "#51bbd6", count: "<10" };
 medium: { size: 50, color: "#f1f075", count: "10-100" };
 large: { size: 60, color: "#f28cb1", count: ">100" };
 };

 spiderfy: {
 enabled: boolean;
 distanceMultiplier: number;
 circleRadius: number;
 };
 };

 onClick: (cluster: Cluster) => void;
 onSpiderfy: (markers: Marker[]) => void;
 };

 individual: {
 icons: {
 producer: {
 url: "/icons/solar-panel.svg";
 size: [30, 30];
 anchor: [15, 30];
 };
 consumer: {
 url: "/icons/house.svg";
 size: [25, 25];
 anchor: [12.5, 25];
 };
 prosumer: {
 url: "/icons/prosumer.svg";
 size: [35, 35];
 anchor: [17.5, 35];
 };
 prospect: {
 url: "/icons/prospect.svg";
 size: [25, 25];
 anchor: [12.5, 25];
 opacity: 0.7;
 };
 };

 states: {
 default: { scale: 1, zIndex: 1 };
 hover: { scale: 1.2, zIndex: 100 };
 selected: { scale: 1.3, zIndex: 200, glow: true };
 };

 popup: {
 offset: [0, -10];
 closeButton: true;
 closeOnClick: false;

 content: (client: Client) => ClientPopupContent;

 actions: [
 { icon: "info", label: "Détails", onClick: (client) => void },
 { icon: "directions", label: "Itinéraire", onClick: (client) => void },
 { icon: "edit", label: "Modifier", onClick: (client) => void }
 ];
 };

 tooltip: {
 permanent: false;
 sticky: false;
 offset: [15, 0];

 content: (client: Client) => string;
 };
 };
 };

 layers: {
 heatmap: {
 data: HeatmapPoint[];

 config: {
 radius: number;
 blur: number;
 maxZoom: number;

 gradient: {
 0.0: "blue";
 0.5: "lime";
 0.8: "yellow";
 1.0: "red";
 };

 weight: {
 property: "revenue" | "consumption" | "potential";
 normalize: boolean;
 };
 };

 legend: {
 position: "bottom-right";
 title: "Densité";
 gradient: boolean;
 labels: string[];
 };
 };

 coverage: {
 zones: Array<{
 id: string;
 name: string;
 geometry: GeoJSON.Polygon;
 properties: {
 type: "served" | "planned" | "potential";
 clients: number;
 potential: number;
 penetration: number;
 };
 style: {
 fillColor: string;
 fillOpacity: number;
 color: string;
 weight: number;
 };
 }>;

 interactions: {
 hover: {
 highlight: boolean;
 showTooltip: boolean;
 };
 click: {
 showDetails: boolean;
 allowEdit: boolean;
 };
 };
 };

 cadastre: {
 enabled: boolean;
 minZoom: 16;

 parcels: {
 source: "cadastre.data.gouv.fr";

 style: {
 default: { color: "#666", weight: 1, fillOpacity: 0 };
 hover: { color: "#000", weight: 2, fillOpacity: 0.1 };
 selected: { color: "#2196F3", weight: 3, fillOpacity: 0.2 };
 };

 data: {
 reference: string;
 surface: number;
 owner: string;
 usage: string;
 };

 actions: {
 select: (parcel: Parcel) => void;
 analyze: (parcel: Parcel) => void;
 createProspect: (parcel: Parcel) => void;
 };
 };
 };

 solarPotential: {
 enabled: boolean;
 source: "pvgis" | "custom";

 raster: {
 url: string;
 bounds: [[number, number], [number, number]];
 opacity: 0.6;
 };

 legend: {
 title: "Potentiel solaire (kWh/m²/an)";
 scale: ColorScale;
 position: "bottom-left";
 };

 analysis: {
 onAreaSelect: (bounds: Bounds) => SolarAnalysis;
 showRoofDetection: boolean;
 calculate3D: boolean;
 };
 };
 };
}
```

### Panneau Latéral d'Analyse
```typescript
interface AnalysisPanel {
 position: "left" | "right";
 width: 350;
 collapsible: boolean;

 tabs: [
 {
 id: "overview";
 label: "Vue d'ensemble";
 icon: "dashboard";

 content: {
 zoneStats: {
 title: "Statistiques de zone";

 metrics: [
 {
 label: "Surface visible";
 value: number;
 unit: "km²";
 },
 {
 label: "Clients";
 value: number;
 breakdown: {
 producers: number;
 consumers: number;
 prospects: number;
 };
 },
 {
 label: "Puissance installée";
 value: number;
 unit: "MWc";
 density: number; // kWc/km²
 },
 {
 label: "Potentiel";
 value: number;
 unit: "MWc";
 opportunities: number;
 }
 ];

 charts: {
 distribution: {
 type: "donut";
 data: ClientDistribution;
 interactive: boolean;
 };

 density: {
 type: "heatbar";
 data: DensityByZone[];
 onClick: (zone: string) => void;
 };
 };
 };

 insights: {
 title: "Insights";

 items: Array<{
 type: "opportunity" | "alert" | "trend";
 title: string;
 description: string;

 location?: [number, number];

 actions: Array<{
 label: string;
 onClick: () => void;
 }>;
 }>;

 autoRefresh: boolean;
 refreshInterval: 300000; // 5 minutes
 };
 };
 },
 {
 id: "selection";
 label: "Sélection";
 icon: "select_all";
 badge?: number; // Nombre d'éléments sélectionnés

 content: {
 tools: {
 shapes: [
 { id: "rectangle", icon: "crop_square" },
 { id: "circle", icon: "circle" },
 { id: "polygon", icon: "pentagon" },
 { id: "radius", icon: "radar" }
 ];

 activeShape: string;

 options: {
 radius: { value: number; unit: "km" | "m" };
 freehand: boolean;
 magnetic: boolean; // Snap to roads/boundaries
 };

 actions: {
 clear: () => void;
 save: () => void;
 load: () => void;
 };
 };

 results: {
 summary: {
 area: number;
 perimeter: number;
 clients: number;
 prospects: number;
 };

 list: {
 items: (Client | Prospect)[];

 groupBy: "type" | "status" | "distance" | null;
 sortBy: "name" | "distance" | "potential" | "created";

 itemActions: [
 { icon: "zoom_in", onClick: (item) => void },
 { icon: "info", onClick: (item) => void },
 { icon: "directions", onClick: (item) => void }
 ];

 bulkActions: {
 visible: boolean;
 actions: [
 { id: "export", label: "Exporter" },
 { id: "assign", label: "Assigner" },
 { id: "campaign", label: "Campagne" }
 ];
 };
 };

 analytics: {
 potential: {
 total: number;
 average: number;
 distribution: PotentialDistribution;
 };

 competition: {
 level: "low" | "medium" | "high";
 competitors: Competitor[];
 marketShare: number;
 };

 demographics: {
 population: number;
 density: number;
 income: IncomeDistribution;
 housing: HousingTypes;
 };
 };
 };
 };
 },
 {
 id: "prospection";
 label: "Prospection";
 icon: "explore";

 content: {
 filters: {
 criteria: [
 {
 id: "roof_surface";
 label: "Surface toiture";
 type: "range";
 value: [100, 1000];
 unit: "m²";
 },
 {
 id: "building_type";
 label: "Type bâtiment";
 type: "select";
 value: string[];
 options: ["Maison", "Immeuble", "Commercial", "Industriel"];
 },
 {
 id: "consumption";
 label: "Consommation estimée";
 type: "range";
 value: [5000, 50000];
 unit: "kWh/an";
 },
 {
 id: "no_competitor";
 label: "Sans concurrent";
 type: "boolean";
 value: boolean;
 }
 ];

 presets: [
 { name: "Résidentiel fort potentiel", filters: FilterPreset },
 { name: "Tertiaire > 500m²", filters: FilterPreset },
 { name: "Zones blanches", filters: FilterPreset }
 ];

 onApply: (filters: Filters) => void;
 onSavePreset: (name: string) => void;
 };

 results: {
 mode: "map" | "list" | "cards";

 prospects: Prospect[];
 loading: boolean;

 scoring: {
 enabled: boolean;

 factors: [
 { name: "potential", weight: 0.3 },
 { name: "accessibility", weight: 0.2 },
 { name: "competition", weight: 0.2 },
 { name: "roi", weight: 0.3 }
 ];

 display: {
 showScore: boolean;
 colorCode: boolean;
 sortByScore: boolean;
 };
 };

 actions: {
 createLead: (prospect: Prospect) => void;
 planRoute: (prospects: Prospect[]) => void;
 exportList: (format: "excel" | "csv") => void;
 createCampaign: (prospects: Prospect[]) => void;
 };
 };

 routes: {
 optimization: {
 start: Location;
 end: Location;
 waypoints: Location[];

 options: {
 optimize: boolean;
 avoidTolls: boolean;
 departureTime: Date;
 visitDuration: number; // minutes par visite
 };

 calculate: () => Route;
 };

 display: {
 route: Route | null;

 style: {
 color: "#2196F3";
 weight: 4;
 opacity: 0.8;
 };

 details: {
 distance: number;
 duration: number;
 visits: Visit[];

 timeline: Timeline;

 export: {
 formats: ["pdf", "ical", "gpx"];
 includeMap: boolean;
 };
 };
 };
 };
 };
 },
 {
 id: "analytics";
 label: "Analyses";
 icon: "analytics";

 content: {
 spatial: {
 title: "Analyses spatiales";

 tools: [
 {
 id: "hotspot";
 label: "Points chauds";
 description: "Identifier les zones à forte concentration";

 run: () => HotspotAnalysis;

 results: {
 visualization: "heatmap" | "points";
 significance: SignificanceLevel[];
 export: boolean;
 };
 },
 {
 id: "accessibility";
 label: "Accessibilité";
 description: "Zones accessibles en X minutes";

 parameters: {
 origin: Location;
 time: number; // minutes
 mode: "driving" | "walking";
 };

 run: () => IschroneAnalysis;
 },
 {
 id: "market_penetration";
 label: "Pénétration marché";
 description: "Taux de pénétration par zone";

 granularity: "commune" | "iris" | "custom";

 run: () => PenetrationAnalysis;
 },
 {
 id: "growth_potential";
 label: "Potentiel croissance";
 description: "Zones à fort potentiel de développement";

 factors: GrowthFactor[];
 weights: number[];

 run: () => GrowthAnalysis;
 }
 ];
 };

 temporal: {
 title: "Évolution temporelle";

 animation: {
 enabled: boolean;

 controls: {
 play: boolean;
 speed: number;
 loop: boolean;
 };

 timeline: {
 start: Date;
 end: Date;
 step: "day" | "week" | "month" | "year";

 markers: TimelineMarker[];
 };

 display: {
 showDate: boolean;
 showLegend: boolean;
 smoothTransitions: boolean;
 };
 };

 trends: {
 metrics: ["client_growth", "production_capacity", "coverage"];

 visualization: {
 type: "line" | "area" | "bar";
 overlay: boolean; // Sur la carte
 };

 predictions: {
 enabled: boolean;
 horizon: number; // mois
 confidence: number;
 };
 };
 };

 comparative: {
 title: "Analyses comparatives";

 scenarios: Array<{
 name: string;
 filters: Filters;
 snapshot: MapSnapshot;
 }>;

 comparison: {
 mode: "side_by_side" | "overlay" | "diff";

 metrics: ComparisonMetric[];

 visualization: {
 synchronize: boolean; // Sync pan/zoom
 highlight: "differences" | "similarities";
 };

 export: {
 format: "pdf" | "pptx";
 includeData: boolean;
 };
 };
 };
 };
 }
 ];
}
```

### Outils et Fonctionnalités
```typescript
interface MapTools {
 measurement: {
 active: boolean;

 tools: {
 distance: {
 icon: "straighten";
 unit: "m" | "km";
 showSegments: boolean;
 };

 area: {
 icon: "square_foot";
 unit: "m²" | "km²" | "ha";
 showPerimeter: boolean;
 };

 radius: {
 icon: "radar";
 center: Location;
 radius: number;
 unit: "m" | "km";
 };
 };

 results: {
 display: "tooltip" | "panel";
 precision: number;

 actions: {
 clear: () => void;
 save: () => void;
 copy: () => void;
 };
 };
 };

 drawing: {
 active: boolean;

 shapes: {
 current: "marker" | "line" | "polygon" | "circle" | "text";

 style: {
 color: string;
 fillColor: string;
 fillOpacity: number;
 weight: number;
 dashArray?: string;
 };

 options: {
 snapToGrid: boolean;
 snapToFeatures: boolean;
 continuousDrawing: boolean;
 };
 };

 annotations: {
 text: {
 font: string;
 size: number;
 color: string;
 background: boolean;
 };

 arrows: boolean;
 labels: boolean;
 };

 layers: {
 drawings: Drawing[];

 management: {
 save: (name: string) => void;
 load: (id: string) => void;
 share: () => ShareLink;
 export: (format: "geojson" | "kml") => void;
 };
 };
 };

 streetView: {
 enabled: boolean;
 provider: "google" | "mapillary";

 viewer: {
 position: "bottom" | "modal";
 size: "small" | "medium" | "large";

 sync: {
 position: boolean;
 heading: boolean;
 };

 features: {
 measure: boolean;
 capture: boolean;
 history: boolean;
 };
 };
 };

 printing: {
 formats: ["A4", "A3", "A2", "Letter"];
 orientations: ["portrait", "landscape"];

 options: {
 title: string;
 scale: boolean;
 legend: boolean;
 northArrow: boolean;
 attribution: boolean;

 quality: "draft" | "normal" | "high";
 format: "pdf" | "png" | "jpg";
 };

 templates: PrintTemplate[];

 preview: {
 show: boolean;
 adjustBounds: boolean;
 };
 };
}
```

## État et données

```typescript
interface CartographyState {
 // Configuration carte
 map: {
 instance: MapInstance;
 view: MapView;
 style: string;

 bounds: Bounds;
 zoom: number;
 center: [number, number];
 };

 // Données
 data: {
 clients: GeoClient[];
 prospects: GeoProspect[];
 clusters: Cluster[];

 loading: boolean;
 lastUpdate: Date;
 };

 // Couches actives
 layers: {
 visible: string[];
 config: Record<string, LayerConfig>;
 custom: CustomLayer[];
 };

 // Sélection
 selection: {
 mode: SelectionMode;
 items: (Client | Prospect)[];
 area?: GeoJSON.Feature;
 };

 // Outils actifs
 tools: {
 active: string | null;
 config: ToolConfig;
 results: any;
 };

 // Analyses
 analysis: {
 running: string[];
 results: Record<string, AnalysisResult>;
 cache: AnalysisCache;
 };

 // UI
 ui: {
 panel: {
 visible: boolean;
 tab: string;
 width: number;
 };

 popup: {
 content: any;
 position: [number, number];
 };

 loading: Record<string, boolean>;
 errors: Error[];
 };
}
```

## API Endpoints

```typescript
// Données géographiques
GET /api/cartography/clients
Query: {
 bounds: [[number, number], [number, number]];
 zoom: number;
 types?: string[];
 cluster?: boolean;
}

// Recherche géographique
GET /api/cartography/search
Query: {
 q: string;
 types: string[];
 bounds?: Bounds;
 limit: number;
}

// Analyses spatiales
POST /api/cartography/analyze
Body: {
 type: string;
 area: GeoJSON.Feature;
 parameters: any;
}

// Prospection
POST /api/cartography/prospects
Body: {
 area: GeoJSON.Feature;
 filters: ProspectFilters;
 scoring?: ScoringConfig;
}

// Export carte
POST /api/cartography/export
Body: {
 bounds: Bounds;
 zoom: number;
 layers: string[];
 format: string;
 options: ExportOptions;
}

// Routing
POST /api/cartography/route
Body: {
 waypoints: Location[];
 optimize: boolean;
 options: RouteOptions;
}

// Données externes
GET /api/cartography/cadastre/:parcelId
GET /api/cartography/solar-potential
GET /api/cartography/demographics
```

## Exemple d'implémentation

```tsx
export const CartographyPage: React.FC = () => {
 const mapRef = useRef<MapInstance>(null);
 const [activeTab, setActiveTab] = useState("overview");
 const [selection, setSelection] = useState<Selection>(null);
 const { clients, clusters, loadData } = useMapData();

 // Initialisation de la carte
 useEffect(() => {
 const map = initializeMap({
 container: "map-container",
 style: "streets",
 center: [2.3522, 48.8566], // Paris
 zoom: 6
 });

 // Ajout des contrôles
 map.addControl(new NavigationControl());
 map.addControl(new ScaleControl());
 map.addControl(new GeolocateControl());

 // Événements
 map.on("moveend", handleMapMove);
 map.on("click", handleMapClick);

 mapRef.current = map;

 return () => map.remove();
 }, []);

 // Chargement des données selon la vue
 useEffect(() => {
 if (mapRef.current) {
 const bounds = mapRef.current.getBounds();
 const zoom = mapRef.current.getZoom();

 loadData({ bounds, zoom, cluster: zoom < 12 });
 }
 }, [map.zoom, map.center]);

 // Gestion de la sélection spatiale
 const handleSelectionComplete = async (area: GeoJSON.Feature) => {
 const results = await analyzeArea(area);
 setSelection({
 area,
 clients: results.clients,
 prospects: results.prospects,
 analytics: results.analytics
 });
 setActiveTab("selection");
 };

 // Analyse de prospection
 const handleProspection = async (filters: ProspectFilters) => {
 const prospects = await findProspects({
 area: selection?.area || getCurrentBounds(),
 filters,
 scoring: {
 factors: ["potential", "accessibility", "competition"],
 weights: [0.4, 0.3, 0.3]
 }
 });

 // Affichage sur la carte
 displayProspects(prospects);

 // Mise à jour du panneau
 updateProspectionResults(prospects);
 };

 // Export de la vue
 const handleExport = async (format: string) => {
 const exportData = await exportMap({
 bounds: mapRef.current.getBounds(),
 zoom: mapRef.current.getZoom(),
 layers: getVisibleLayers(),
 format,
 options: {
 title: "Carte des clients OptimPV",
 legend: true,
 scale: true
 }
 });

 downloadFile(exportData);
 };

 return (
 <CartographyLayout>
 <CartographyHeader
 onSearch={handleSearch}
 onLayerToggle={handleLayerToggle}
 onToolSelect={handleToolSelect}
 />

 <MapContainer>
 <InteractiveMap
 ref={mapRef}
 clients={clients}
 clusters={clusters}
 onSelectionComplete={handleSelectionComplete}
 />

 <AnalysisPanel
 activeTab={activeTab}
 onTabChange={setActiveTab}
 selection={selection}
 onProspection={handleProspection}
 onAnalyze={handleAnalyze}
 />

 {tools.active && (
 <MapTools
 tool={tools.active}
 config={tools.config}
 onComplete={handleToolComplete}
 />
 )}
 </MapContainer>
 </CartographyLayout>
 );
};
```