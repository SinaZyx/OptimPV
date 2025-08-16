# Page Carte Interactive - Module Prospect Mapping

## Vue d'ensemble

La carte interactive de prospection photovoltaïque du département 06 (Alpes-Maritimes) basée sur les données Enedis Open Data avec géocodage, enrichissement BD TOPO et intégration DPE.

## Structure de la page

### Header Principal
```typescript
interface MapHeader {
 title: {
 main: " Carte de Prospection - Département 06";
 description: "Cartographie interactive des données de consommation énergétique des bâtiments des Alpes-Maritimes pour identifier les prospects solaires";
 };

 refreshButton: {
 label: " Actualiser les Données";
 tooltip: "Vide le cache et recharge les données depuis l'API Enedis";
 type: "secondary";
 onClick: () => {
 load_and_process_data.clear();
 showSuccess(" Cache vidé! Les données vont être rechargées.");
 rerun();
 };
 };
}
```

### Section Sélection des Communes
```typescript
interface CommuneSelection {
 title: " Sélection des Communes";

 loadingModes: [
 {
 id: "proximity_mougins";
 label: " Proximité Mougins (10 communes les plus proches) - RECOMMANDÉ";
 description: "Centré sur Mougins, inclut Cannes, Antibes, Le Cannet, Vallauris, etc.";
 estimatedAddresses: 2000;
 estimatedTime: "15-30 secondes";
 default: true;

 config: {
 center: { latitude: 43.5974, longitude: 7.0058, nom: "Mougins" };
 proximityMode: true;
 communes: string[];
 };
 },
 {
 id: "custom_selection";
 label: " Sélection personnalisée";
 description: "Sélectionnez quelques communes pour un téléchargement plus rapide!";

 multiSelect: {
 label: "Communes à télécharger";
 options: string[]; // from get_all_communes_dept_06()
 value: string[];
 placeholder: "Sélectionnez une ou plusieurs communes";
 help: "Sélectionnez une ou plusieurs communes pour télécharger et afficher leurs données";

 estimation: {
 recordsPerCommune: 200;
 timeRange: "30 secondes - 2 minutes";
 };
 };
 },
 {
 id: "all_communes";
 label: " Toutes les communes du 06";
 warning: " Attention: Toutes les communes = 10,000+ adresses, temps: 5-10 minutes";
 proximityMode: false;
 }
 ];

 dataLoader: {
 function: "load_and_process_data";
 params: {
 communes_filter?: string[];
 proximity_mode: boolean;
 };
 cache: {
 enabled: true;
 ttl: 3600; // 1 hour
 };
 };
}
```

### Section Recherche par Adresse/GPS
```typescript
interface AddressGPSSearch {
 title: " Recherche par Adresse ou Coordonnées GPS";

 searchModes: [
 {
 id: "address";
 label: " Adresse";

 addressInput: {
 placeholder: "Ex: 123 Avenue des Fleurs, Mougins";
 help: "L'adresse sera géocodée pour obtenir les coordonnées GPS";

 searchButton: {
 label: " Rechercher l'adresse";
 type: "primary";
 onClick: async () => {
 const result = await search_and_geocode_address(searchAddress);
 if (result.success) {
 setSessionState('search_location', {
 latitude: result.latitude,
 longitude: result.longitude,
 address: result.address_found
 });
 showSuccess(` Adresse trouvée: ${result.address_found}`);
 showInfo(` Coordonnées: ${result.latitude:.6f}, ${result.longitude:.6f}`);
 } else {
 showError(` Adresse non trouvée: ${result.error}`);
 }
 };
 };
 };
 },
 {
 id: "gps";
 label: " Coordonnées GPS";

 inputModes: [
 {
 id: "single_field";
 label: "Une seule case";

 coordsInput: {
 placeholder: "43.631241005708134, 6.9373580224334495";
 help: "Format: latitude, longitude (séparées par une virgule)";
 validation: {
 bounds: { lat: [43.0, 44.5], lon: [6.5, 7.8] };
 department: "06";
 };
 };
 },
 {
 id: "separate_fields";
 label: "Deux cases séparées";

 latitudeInput: {
 min: 43.0;
 max: 44.5;
 value: 43.5974;
 step: 0.0001;
 format: "%.6f";
 };

 longitudeInput: {
 min: 6.5;
 max: 7.8;
 value: 7.0058;
 step: 0.0001;
 format: "%.6f";
 };
 }
 ];
 }
 ];
}
```

### Section Affichage DPE
```typescript
interface DPEDisplay {
 title: " Affichage DPE";

 showDPEMarkers: {
 type: "checkbox";
 label: "Afficher les DPE";
 value: false;
 help: "Affiche tous les DPE disponibles autour du point recherché";
 };

 dpeRadius: {
 type: "slider";
 label: "Rayon de recherche (m)";
 min: 100;
 max: 1000;
 value: 500;
 step: 100;
 help: "Distance de recherche des DPE autour du point";
 visible: boolean; // when showDPEMarkers is true
 };

 buildingTypeFilter: {
 type: "multiselect";
 label: "Types de bâtiments";
 options: ["Tous", "appartement", "immeuble", "maison"];
 default: ["Tous"];
 help: "Filtrer par type de bâtiment";
 visible: boolean; // when showDPEMarkers is true
 };

 externalLinks: [
 {
 label: " Observatoire DPE";
 url: "https://observatoire-dpe-audit.ademe.fr/accueil";
 help: "Accéder à l'observatoire national";
 type: "link_button";
 },
 {
 label: " Vider cache DPE";
 help: "Forcer le rechargement des données DPE";
 onClick: () => {
 get_all_dpe_around_point.clear();
 showSuccess(" Cache DPE vidé!");
 rerun();
 };
 }
 ];

 dpeSearchFunction: {
 name: "get_all_dpe_around_point";
 params: {
 latitude: number;
 longitude: number;
 radius: number;
 };
 filtering: {
 byBuildingType: (dpe_data: DataFrame, types: string[]) => DataFrame;
 };
 cache: {
 enabled: true;
 clearable: true;
 };
 };
}
```

### Statistiques Temps Réel (5 métriques)
```typescript
interface RealTimeStats {
 layout: "5_columns";

 metrics: [
 {
 id: "total_points";
 label: "Total Points";
 value: number;
 delta?: number; // différence après filtrage
 format: "{value:,}";
 },
 {
 id: "average_consumption";
 label: "Consommation Moyenne";
 value: number;
 unit: "kWh";
 calculation: "filtered_data['consommation_kwh'].mean()";
 format: "{value:,.0f} kWh";
 },
 {
 id: "total_consumption";
 label: "Consommation Totale";
 value: number;
 unit: "MWh";
 calculation: "filtered_data['consommation_kwh'].sum() / 1000";
 format: "{value:,.0f} MWh";
 },
 {
 id: "communes_displayed";
 label: "Communes Affichées" | "Communes Sélectionnées";
 value: number;
 calculation: "filtered_data['nom_commune'].nunique()" | "len(selected_communes)";
 },
 {
 id: "precision_quality";
 label: " Précision";
 status: "Bonne" | "Moyenne" | "Basique";
 icon: "" | "" | "";
 calculation: {
 highPrecision: "(filtered_data['location_confidence'] == 'high').sum()";
 osmPrecision: "(filtered_data['data_source'] == 'OSM').sum()";
 qualityRate: "(quality_points / total_points * 100)";

 thresholds: {
 good: 30; // >= 30%
 average: 10; // >= 10%
 basic: 0; // < 10%
 };
 };
 delta: "{quality_points}/{total_points}";
 }
 ];
}
```

### Configuration de Carte Simplifiée
```typescript
interface MapConfiguration {
 title: " Configuration de la Carte";
 expandable: true;
 expanded: false;

 sections: {
 styleControls: {
 mapStyle: {
 label: " Style de fond";
 type: "selectbox";
 options: [
 "Cadastral", // DEFAULT
 "Plan Standard",
 "Satellite",
 "Satellite + Rues",
 "Sombre",
 "OpenStreetMap"
 ];
 default: "Cadastral";
 help: "Cadastral recommandé pour la prospection";
 };

 colorBy: {
 label: " Colorer selon";
 type: "selectbox";
 options: ["Consommation", "Nombre de logements", "Surface estimée"];
 default: "Consommation";
 };
 };

 displayControls: {
 opacity: {
 label: " Transparence";
 type: "slider";
 min: 0;
 max: 100;
 value: 70;
 format: "%d%%";
 };

 showBorders: {
 label: "Afficher contours";
 type: "checkbox";
 value: true;
 };
 };

 apiKey: {
 mapboxKey: {
 label: " Clé Mapbox (optionnelle)";
 type: "text_input";
 inputType: "password";
 help: "Pour les styles satellite";
 };
 };

 actions: {
 export: {
 label: " Exporter";
 onClick: () => showInfo("Export en cours...");
 useContainerWidth: true;
 };
 };
 };
}
```

### Filtres de Prospection
```typescript
interface ProspectionFilters {
 title: " Filtres de Prospection";

 consumptionFilter: {
 label: "Consommation annuelle (kWh)";
 type: "range_slider";

 calculation: {
 min: "data['consommation_kwh'].min()";
 max: "data['consommation_kwh'].max()";
 mean: "data['consommation_kwh'].mean()";
 };

 slider: {
 min: "int(min_consumption)";
 max: "int(max_consumption)";
 value: "[int(min_consumption), int(max_consumption)]";
 step: 1000;
 format: "%d kWh";
 };

 caption: "De {consumption_range[0]:,} à {consumption_range[1]:,} kWh/an";
 };

 housingFilter: {
 label: "Nombre de logements";
 type: "range_slider";

 calculation: {
 min: "int(data['nombre_de_logements'].min())";
 max: "int(data['nombre_de_logements'].max())";
 };

 slider: {
 min: "min_logements";
 max: "max_logements";
 value: "[min_logements, max_logements]";
 };

 caption: "De {logements_range[0]} à {logements_range[1]} logements";
 visible: "'nombre_de_logements' in data.columns";
 };

 filterApplication: {
 consumptionFiltering: """
 filtered_data = filtered_data[
 (filtered_data['consommation_kwh'] >= consumption_range[0]) &
 (filtered_data['consommation_kwh'] <= consumption_range[1])
 ]
 """;

 housingFiltering: """
 if logements_range and 'nombre_de_logements' in filtered_data.columns:
 filtered_data = filtered_data[
 (filtered_data['nombre_de_logements'] >= logements_range[0]) &
 (filtered_data['nombre_de_logements'] <= logements_range[1])
 ]
 """;
 };
}
```

### Légende Compacte
```typescript
interface CompactLegend {
 layout: "4_columns";

 metrics: [
 {
 id: "min_consumption";
 icon: "";
 label: "Min";
 value: "legend_info['min_consumption']";
 format: "{value:,.0f} kWh";
 },
 {
 id: "mean_consumption";
 icon: "";
 label: "Moyenne";
 value: "legend_info['mean_consumption']";
 format: "{value:,.0f} kWh";
 },
 {
 id: "max_consumption";
 icon: "";
 label: "Max";
 value: "legend_info['max_consumption']";
 format: "{value:,.0f} kWh";
 },
 {
 id: "total_points";
 icon: "";
 label: "Points";
 value: "len(filtered_data)";
 format: "{value:,}";
 }
 ];

 calculation: "legend_info = get_map_legend_info(filtered_data)";
}
```

### Carte Interactive Principale
```typescript
interface InteractiveMap {
 mapGenerator: {
 function: "create_prospect_map";
 params: {
 map_data: DataFrame;
 mapbox_api_key?: string;
 interaction_mode: "Navigation";
 tooltip_mode: "Survol normal";
 map_style: string; // "Cadastral" par défaut
 opacity: number; // 0.7 par défaut
 show_borders: boolean; // true par défaut
 color_by: string; // "Consommation" par défaut
 dpe_data?: DataFrame;
 show_dpe: boolean;
 search_location?: SearchLocation;
 erp_client_data?: any;
 show_erp_clients: boolean;
 };
 returns: "pydeck.Deck";
 };

 display: {
 component: "st.pydeck_chart";
 params: {
 map_obj: "pydeck.Deck";
 use_container_width: true;
 key: "prospect_map";
 };
 };

 dataPreparation: {
 adaptiveSize: {
 enabled: true;
 zoomCalculation: "14 - int(lat_range * 10)";
 boundsCalculation: "max(9, min(14, estimated_zoom))";
 polygonUpdate: "update_polygons_for_zoom(map_data, estimated_zoom)";
 };

 indexReset: "map_data = map_data.reset_index(drop=True)";

 dpeIntegration: {
 condition: "show_dpe_markers and 'search_location' in st.session_state";
 function: "get_all_dpe_around_point";
 filtering: "dpe_data[dpe_data['type_batiment'].isin(dpe_types)]";
 };
 };
}
```

### Sélection de Parcelle
```typescript
interface ParcelSelector {
 title: " Sélection de Parcelle";

 parcelDropdown: {
 type: "selectbox";
 label: "Choisissez une parcelle pour voir les détails";

 options: {
 generation: """
 for idx, row in display_data.iterrows():
 numero_parcelle = row.get('numero_parcelle', idx + 1)
 label = f"Parcelle #{numero_parcelle} - {row.get('nom_commune', 'N/A')} - {row.get('consommation_kwh', 0):,.0f} kWh"
 parcel_options.append((label, idx))
 """;

 placeholder: "-- Sélectionnez une parcelle --";
 };

 sessionState: {
 key: "selected_parcel_index";
 onSelect: "st.session_state.selected_parcel_index = selected_option[1]";
 };
 };

 parcelDetails: {
 visible: "st.session_state.selected_parcel_index is not None";

 basicInfo: {
 commune: "selected_parcel.get('nom_commune', 'N/A')";
 address: "selected_parcel.get('adresse', 'N/A')";
 housing: "selected_parcel.get('nombre_de_logements', 0)";
 consumption: "selected_parcel.get('consommation_kwh', 0)";
 coordinates: "selected_parcel.get('latitude', 0), selected_parcel.get('longitude', 0)";
 };

 buildingEnrichment: {
 availableColumns: [
 'location_confidence', 'data_source', 'nature_detaillee',
 'nb_etages', 'etat_batiment', 'date_construction',
 'dpe_available', 'dpe_classe_energie', 'dpe_classe_ges'
 ];

 enrichmentFunction: {
 name: "enrich_single_building_on_demand";
 params: {
 lat: "selected_parcel.get('latitude', 0)";
 lon: "selected_parcel.get('longitude', 0)";
 building_id: "f'{lat:.6f}_{lon:.6f}'";
 };

 onDemandTrigger: " Enrichir cette parcelle";

 results: {
 osm_data: ['nature_detaillee', 'nb_etages', 'etat_batiment', 'date_construction', 'location_confidence', 'data_source'];
 dpe_data: ['dpe_classe_energie', 'dpe_classe_ges', 'dpe_consommation', 'dpe_distance'];
 };
 };
 };

 externalLinks: {
 googleEarth: {
 label: " Vue 3D";
 url: "https://earth.google.com/web/search/{latitude},{longitude}";
 };

 googleMaps: {
 label: " Localisation";
 url: "https://www.google.com/maps?q={latitude},{longitude}";
 };
 };
 };
}
```

### Simulateur Solaire Intégré
```typescript
interface SolarSimulator {
 title: " Simulateur Solaire Simplifié";
 approach: "Nouvelle approche simplifiée: Mesurez la surface avec Google Earth, entrez la valeur, obtenez tous les calculs!";

 tabs: [
 {
 id: "google_earth_guide";
 title: " Étape 1: Guide Google Earth";

 instructions: {
 steps: [
 "Ouvrir Google Earth (gratuit) - earth.google.com",
 "Localiser le bâtiment - Recherchez l'adresse exacte",
 "Mesurer la surface - Outil 'Mesurer' > 'Mesurer une zone'",
 "Noter la surface - Google Earth affiche la surface en m²"
 ];

 directLink: {
 url: "https://earth.google.com/web/@{lat},{lon},200a,1000d,35y,0h,0t,0r";
 coordinates: "selected_parcel['latitude'], selected_parcel['longitude']";
 };
 };
 },
 {
 id: "solar_simulation";
 title: " Étape 2: Simulation Solaire";

 inputs: {
 surfaceInput: {
 label: "Surface (m²)";
 type: "number_input";
 min: 0.0;
 max: 50000.0;
 value: 100.0;
 step: 5.0;

 surfaceType: {
 options: ['brute', 'nette'];
 labels: [' Brute', ' Nette'];
 help: "Brute = Google Earth total | Nette = zones panneaux uniquement";
 };
 };

 calculationApproach: {
 label: "Niveau de confiance";
 options: ['optimiste', 'realiste', 'conservateur'];
 labels: [' 90%', ' 83%', ' 75%'];
 default: 'realiste';
 };

 buildingType: {
 label: "Type de bâtiment";
 options: [
 'residential_family', 'residential_telework', 'office',
 'retail', 'industrial_2x8', 'industrial_3x8'
 ];
 labels: [
 ' Famille', ' Télétravail', ' Bureaux',
 ' Commerce', ' Industrie 2x8', ' Industrie 3x8'
 ];
 };

 orientation: {
 tilt: { options: [0, 15, 30, 45], default: 30, unit: "°" };
 azimuth: {
 options: [135, 180, 225],
 labels: ["SE", "Sud", "SO"],
 default: 180
 };
 };

 consumption: {
 label: "Consommation (kWh/an)";
 default: "selected_parcel['consommation_kwh']";
 min: 1000;
 max: 1000000;
 step: 1000;
 };
 };

 calculation: {
 function: "SolarSimulator.calculate_advanced_autoconsumption";
 params: {
 annual_consumption: number;
 kwp: number; // from calculate_panels_from_area
 lat: number;
 lon: number;
 azimuth: number;
 tilt: number;
 building_type: string;
 custom_profile?: object;
 };

 panelCalculation: {
 function: "simulator.calculate_panels_from_area";
 params: { surface_m2: number, approach: string };
 returns: { total_kwc: number, total_panels: number, layout: object };
 };

 pvgisIntegration: {
 api: "Commission Européenne";
 analysis: "8760 heures";
 profiles: "ADEME/RTE France";
 };
 };

 results: {
 summary: {
 production_annual_kwh: number;
 self_consumption_rate: number;
 self_production_rate: number;
 autoconsumption_kwh: number;
 grid_consumption_kwh: number;
 };

 layout: {
 total_panels: number;
 total_kwc: number;
 alternatives?: object;
 calculation_detail?: object;
 efficiency_preset?: object;
 };

 financial: {
 cout_installation: number;
 annual_savings: number;
 roi_years: number;
 savings_20_years: number;
 };

 sessionStorage: "st.session_state.solar_results_advanced";
 };
 }
 ];
}
```

## Structure des données réelles

```typescript
// Données principales (Enedis Open Data)
interface ProspectData {
 // Champs obligatoires
 consommation_kwh: number; // Consommation annuelle en kWh
 nom_commune: string; // Nom de la commune
 latitude: number; // Coordonnées GPS latitude
 longitude: number; // Coordonnées GPS longitude
 adresse: string; // Adresse complète
 nombre_de_logements: number; // Nombre de logements dans le bâtiment

 // Champs optionnels (enrichissement BD TOPO)
 location_confidence?: 'high' | 'medium' | 'low';
 data_source?: 'OSM' | 'Estimation';
 nature_detaillee?: string; // Type de bâtiment détaillé
 nb_etages?: number;
 etat_batiment?: string;
 date_construction?: string;

 // Champs DPE (si disponible)
 dpe_available?: boolean;
 dpe_classe_energie?: 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G';
 dpe_classe_ges?: 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G';
 dpe_consommation?: number; // kWh/m²/an
 dpe_distance?: number; // Distance en mètres du DPE le plus proche

 // Champs géométriques (pour la carte)
 polygon?: GeoJSONGeometry;
 numero_parcelle?: number; // Index pour l'affichage
}

// Configuration départementale
interface DepartmentConfig {
 department: '06'; // Alpes-Maritimes
 bounds: {
 latitude: [43.0, 44.5];
 longitude: [6.5, 7.8];
 };

 mougins_center: {
 latitude: 43.5974;
 longitude: 7.0058;
 nom: 'Mougins';
 };

 data_sources: {
 enedis_api: 'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/records';
 communes_api: 'https://geo.api.gouv.fr/communes';
 geocoding_api: 'https://api-adresse.data.gouv.fr/search/';
 dpe_api: 'https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines';
 };
}

// État de l'application
interface MapState {
 data: ProspectData[];
 filteredData: ProspectData[];
 selectedParcelIndex: number | null;
 searchLocation?: {
 latitude: number;
 longitude: number;
 address: string;
 };

 loadingMode: 'proximity_mougins' | 'custom_selection' | 'all_communes';
 communesFilter: string[] | null;
 proximityMode: boolean;

 showDpeMarkers: boolean;
 dpeRadius: number; // 100-1000m
 dpeTypes: string[];
 dpeData?: DataFrame;

 mapConfig: {
 style: string; // 'Cadastral' par défaut
 colorBy: string; // 'Consommation' par défaut
 opacity: number; // 70% par défaut
 showBorders: boolean; // true par défaut
 };

 filters: {
 consumptionRange: [number, number];
 housingRange?: [number, number];
 };
}
```

## Fonctions et API intégrées

```typescript
// Fonctions principales du data_handler
interface DataHandlerFunctions {
 // Chargement et traitement des données
 load_and_process_data: {
 params: {
 communes_filter?: string[];
 proximity_mode: boolean;
 };
 returns: ProspectData[];
 cache: {
 enabled: true;
 ttl: 3600; // 1 heure
 clearable: true;
 };
 };

 // Récupération des communes
 get_unique_communes: () => string[];
 get_all_communes_dept_06: () => string[];
 get_closest_communes_to_mougins: () => string[];

 // Filtrage des données
 filter_data_by_consumption: {
 params: { data: DataFrame, threshold: number };
 returns: DataFrame;
 };

 filter_data_by_communes: {
 params: { data: DataFrame, communes: string[] };
 returns: DataFrame;
 };

 // Géocodage et recherche
 search_and_geocode_address: {
 params: { address: string };
 returns: {
 success: boolean;
 latitude?: number;
 longitude?: number;
 address_found?: string;
 error?: string;
 };
 };

 // DPE
 get_all_dpe_around_point: {
 params: {
 latitude: number;
 longitude: number;
 radius: number;
 };
 returns: DataFrame | null;
 cache: {
 enabled: true;
 clearable: true;
 };
 };

 // Enrichissement bâtiment
 enrich_single_building_on_demand: {
 params: {
 lat: number;
 lon: number;
 building_id: string;
 };
 returns: {
 data_source: string;
 nature_detaillee?: string;
 nb_etages?: number;
 etat_batiment?: string;
 date_construction?: string;
 location_confidence?: string;
 dpe_available?: boolean;
 dpe_classe_energie?: string;
 dpe_classe_ges?: string;
 dpe_consommation?: number;
 dpe_distance?: number;
 };
 };

 // Géométrie et polygones
 update_polygons_for_zoom: {
 params: { data: DataFrame, zoom_level: number };
 returns: DataFrame;
 };
}

// APIs externes utilisées
interface ExternalAPIs {
 enedis: {
 url: 'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/records';
 filters: {
 where: "code_departement='06'";
 communes?: string[];
 };
 };

 geocoding: {
 url: 'https://api-adresse.data.gouv.fr/search/';
 params: { q: string };
 };

 dpe: {
 url: 'https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines';
 spatial_search: {
 latitude: number;
 longitude: number;
 radius: number;
 };
 };
}
```

## Implémentation React/TypeScript

```tsx
import React, { useState, useEffect } from 'react';
import { ProspectData, MapState, DepartmentConfig } from '@/types/prospect-mapping';
import {
 CommuneSelector,
 AddressGPSSearch,
 DPEDisplay,
 RealTimeStats,
 MapConfiguration,
 ProspectionFilters,
 InteractiveMap,
 ParcelSelector
} from '@/components/prospect-mapping';

export const ProspectMapPage: React.FC = () => {
 const [mapState, setMapState] = useState<MapState>({
 data: [],
 filteredData: [],
 selectedParcelIndex: null,
 loadingMode: 'proximity_mougins',
 communesFilter: null,
 proximityMode: true,
 showDpeMarkers: false,
 dpeRadius: 500,
 dpeTypes: ['Tous'],
 mapConfig: {
 style: 'Cadastral',
 colorBy: 'Consommation',
 opacity: 70,
 showBorders: true
 },
 filters: {
 consumptionRange: [0, 100000]
 }
 });

 const [loading, setLoading] = useState(false);

 // Chargement des données selon le mode sélectionné
 const loadData = async () => {
 setLoading(true);
 try {
 // Équivalent à load_and_process_data(communes_filter, proximity_mode)
 const data = await loadAndProcessData(
 mapState.communesFilter,
 mapState.proximityMode
 );

 setMapState(prev => ({...prev, data, filteredData: data }));
 } catch (error) {
 console.error('Erreur chargement données:', error);
 } finally {
 setLoading(false);
 }
 };

 // Application des filtres
 useEffect(() => {
 let filtered = mapState.data;

 // Filtre consommation
 const [minConso, maxConso] = mapState.filters.consumptionRange;
 filtered = filtered.filter(item =>
 item.consommation_kwh >= minConso &&
 item.consommation_kwh <= maxConso
 );

 // Filtre logements si défini
 if (mapState.filters.housingRange) {
 const [minLog, maxLog] = mapState.filters.housingRange;
 filtered = filtered.filter(item =>
 item.nombre_de_logements >= minLog &&
 item.nombre_de_logements <= maxLog
 );
 }

 setMapState(prev => ({...prev, filteredData: filtered }));
 }, [mapState.data, mapState.filters]);

 // Calcul des statistiques temps réel
 const stats = {
 totalPoints: mapState.filteredData.length,
 avgConsumption: mapState.filteredData.length > 0?
 mapState.filteredData.reduce((sum, item) => sum + item.consommation_kwh, 0) / mapState.filteredData.length: 0,
 totalConsumption: mapState.filteredData.reduce((sum, item) => sum + item.consommation_kwh, 0) / 1000, // MWh
 uniqueCommunes: new Set(mapState.filteredData.map(item => item.nom_commune)).size,
 precisionQuality: calculatePrecisionQuality(mapState.filteredData)
 };

 return (
 <div className="prospect-map-page">
 {/* Header principal */}
 <div className="header-section">
 <div className="title-section">
 <h1> Carte de Prospection - Département 06</h1>
 <p>Cette carte interactive affiche les données de consommation énergétique des bâtiments
 du département des Alpes-Maritimes (06) pour identifier les prospects potentiels
 pour l'installation de panneaux solaires.</p>
 </div>
 <div className="refresh-section">
 <button
 className="refresh-btn"
 onClick={() => {
 // Équivalent à load_and_process_data.clear()
 clearDataCache();
 loadData();
 }}
 >
 Actualiser les Données
 </button>
 </div>
 </div>

 {/* Sélection des communes */}
 <CommuneSelector
 loadingMode={mapState.loadingMode}
 onModeChange={(mode) => setMapState(prev => ({...prev, loadingMode: mode }))}
 communesFilter={mapState.communesFilter}
 onCommunesChange={(communes) => setMapState(prev => ({...prev, communesFilter: communes }))}
 onLoadData={loadData}
 loading={loading}
 />

 {/* Recherche par adresse/GPS */}
 <AddressGPSSearch
 searchLocation={mapState.searchLocation}
 onLocationSet={(location) => setMapState(prev => ({...prev, searchLocation: location }))}
 />

 {/* Affichage DPE */}
 <DPEDisplay
 showDpeMarkers={mapState.showDpeMarkers}
 onToggleDpe={(show) => setMapState(prev => ({...prev, showDpeMarkers: show }))}
 dpeRadius={mapState.dpeRadius}
 onRadiusChange={(radius) => setMapState(prev => ({...prev, dpeRadius: radius }))}
 dpeTypes={mapState.dpeTypes}
 onTypesChange={(types) => setMapState(prev => ({...prev, dpeTypes: types }))}
 searchLocation={mapState.searchLocation}
 />

 {/* Statistiques temps réel */}
 <RealTimeStats stats={stats} />

 {/* Configuration carte */}
 <MapConfiguration
 mapConfig={mapState.mapConfig}
 onConfigChange={(config) => setMapState(prev => ({
...prev,
 mapConfig: {...prev.mapConfig,...config }
 }))}
 />

 {/* Filtres de prospection */}
 <ProspectionFilters
 data={mapState.data}
 filters={mapState.filters}
 onFiltersChange={(filters) => setMapState(prev => ({
...prev,
 filters: {...prev.filters,...filters }
 }))}
 />

 {/* Carte interactive principale */}
 <InteractiveMap
 data={mapState.filteredData}
 mapConfig={mapState.mapConfig}
 searchLocation={mapState.searchLocation}
 dpeData={mapState.dpeData}
 showDpeMarkers={mapState.showDpeMarkers}
 onParcelSelect={(index) => setMapState(prev => ({...prev, selectedParcelIndex: index }))}
 />

 {/* Sélecteur de parcelle */}
 <ParcelSelector
 data={mapState.filteredData}
 selectedIndex={mapState.selectedParcelIndex}
 onSelect={(index) => setMapState(prev => ({...prev, selectedParcelIndex: index }))}
 onEnrichBuilding={enrichBuildingOnDemand}
 />
 </div>
 );
};

// Fonctions utilitaires
const calculatePrecisionQuality = (data: ProspectData[]) => {
 if (data.length === 0) return { status: 'Analyse...', icon: '', qualityPoints: 0, totalPoints: 0 };

 const highPrecision = data.filter(item => item.location_confidence === 'high').length;
 const osmPrecision = data.filter(item => item.data_source === 'OSM').length;
 const qualityPoints = highPrecision + osmPrecision;
 const qualityRate = (qualityPoints / data.length) * 100;

 let status, icon;
 if (qualityRate >= 30) {
 status = 'Bonne';
 icon = '';
 } else if (qualityRate >= 10) {
 status = 'Moyenne';
 icon = '';
 } else {
 status = 'Basique';
 icon = '';
 }

 return { status, icon, qualityPoints, totalPoints: data.length };
};
```

## Fonctionnalités clés

### 1. **Chargement optimisé des données**
- **Mode Proximité Mougins**: 10 communes les plus proches (~2000 adresses, 15-30s)
- **Sélection personnalisée**: Communes au choix (estimation dynamique)
- **Toutes les communes**: Département complet (10,000+ adresses, 5-10min)
- **Cache intelligent**: Données mises en cache 1 heure, vidage manuel possible

### 2. **Géocodage et recherche spatiale**
- **Recherche par adresse**: API adresse.data.gouv.fr avec validation département 06
- **Coordonnées GPS**: Saisie simple ou séparée avec validation des limites
- **Validation géographique**: Lat: 43.0-44.5, Lon: 6.5-7.8

### 3. **Intégration DPE (Diagnostic de Performance Énergétique)**
- **Rayon configurable**: 100-1000m autour du point recherché
- **Filtrage par type**: appartement, immeuble, maison
- **Classes énergétiques**: A-G avec code couleur
- **Cache DPE**: Données mises en cache, vidage manuel

### 4. **Cartographie intelligente**
- **Styles adaptatifs**: Cadastral (recommandé), Satellite, Plan, etc.
- **Coloration dynamique**: Par consommation, nombre de logements, surface
- **Transparence réglable**: 0-100% pour superposition couches
- **Polygones adaptatifs**: Taille selon zoom (15-100m)

### 5. **Enrichissement à la demande**
- **Données BD TOPO**: Type bâtiment, étages, état, date construction
- **Données OSM**: Informations complémentaires géographiques
- **Indicateurs qualité**: Précision haute/moyenne/basique
- **Sources multiples**: Enedis + IGN + OpenStreetMap + ADEME

### 6. **Simulation solaire intégrée**
- **Mesure Google Earth**: Guide pour mesurer surface toiture
- **Profils de consommation**: Famille, télétravail, bureau, industrie
- **Calcul PVGIS**: Données météo européennes officielles
- **Analyse 8760h**: Calcul heure par heure sur une année
- **ROI financier**: Coût installation, économies, retour investissement

## Données et cache

```typescript
// Gestion du cache
interface CacheManagement {
 dataCache: {
 function: 'load_and_process_data';
 ttl: 3600; // 1 heure
 clearTrigger: 'refresh_button';
 };

 dpeCache: {
 function: 'get_all_dpe_around_point';
 ttl: 86400 * 30; // 30 jours
 clearTrigger: 'dpe_refresh_button';
 };

 geocodingCache: {
 ttl: 86400 * 7; // 7 jours
 reason: 'Les adresses ne changent pas';
 };
}

// Structure des données temps réel
interface LiveDataStructure {
 source: 'Enedis Open Data API';
 updateFrequency: 'Annual';
 fields: {
 required: ['consommation_kwh', 'nom_commune', 'latitude', 'longitude', 'adresse', 'nombre_de_logements'];
 enriched: ['location_confidence', 'data_source', 'nature_detaillee', 'nb_etages', 'dpe_*'];
 };

 department: {
 code: '06';
 name: 'Alpes-Maritimes';
 communes: 163;
 estimatedBuildings: 100000;
 };
}
```

## Configuration technique

- **API Enedis**: consommation-annuelle-residentielle-par-adresse
- **API Géocodage**: api-adresse.data.gouv.fr
- **API DPE**: data.ademe.fr (dpe-v2-logements-existants)
- **Cartographie**: Pydeck + Streamlit avec support Mapbox optionnel
- **Cache**: Streamlit session state + decorateurs @st.cache_data
- **Géométrie**: Polygones carrés adaptatifs selon zoom
- **Performance**: Virtualisation pour >10k points