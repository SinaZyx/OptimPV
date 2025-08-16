# Configuration Projet & Technique

## Vue d'ensemble

La page de configuration technique permet de paramétrer tous les aspects techniques d'un projet photovoltaïque: caractéristiques de l'installation, localisation, technologie des panneaux, configuration électrique, et estimations de production avec validation en temps réel.

## Structure de la page

### Header de Configuration
```typescript
interface ProjectTechnicalHeader {
 title: " Projet & Technique";

 projectOverview: {
 name: string;
 power: number;
 location: string;
 technology: string;

 status: {
 technical: "incomplete" | "draft" | "validated";
 production: "calculating" | "estimated" | "validated";
 warnings: number;
 };

 keyMetrics: {
 production: {
 annual: number;
 specific: number;
 unit: "MWh/an" | "kWh/kWc/an";
 };

 performance: {
 ratio: number;
 efficiency: number;
 unit: "%";
 };
 };
 };

 actions: {
 calculator: {
 label: "Calculateur production";
 icon: "calculate";
 onClick: () => void;
 };

 optimizer: {
 label: "Optimiseur configuration";
 icon: "tune";
 onClick: () => void;
 };

 import: {
 label: "Importer étude";
 formats: [".pdf", ".xlsx", ".json"];
 onImport: (file: File) => void;
 };
 };
}
```

### Section Installation Générale
```typescript
interface GeneralInstallationSection {
 title: " Installation générale";

 fields: {
 puissanceCrete: {
 label: "Puissance crête totale";
 type: "number";
 value: number;
 unit: "kWc";
 required: true;

 input: {
 min: 0.1;
 max: 50000;
 step: 0.1;
 precision: 2;
 };

 validation: {
 minResidential: 3;
 maxResidential: 36;
 minCommercial: 36;
 maxCommercial: 1000;

 warnings: {
 oversized: boolean;
 undersized: boolean;
 optimal: boolean;
 };
 };

 helpers: {
 calculator: {
 label: "Calculer depuis panneaux";

 dialog: {
 panelSelection: {
 brand: string;
 model: string;
 unitPower: number;
 efficiency: number;

 library: {
 search: string;
 categories: PanelCategory[];
 favorites: Panel[];
 };
 };

 configuration: {
 quantity: number;
 arrangement: {
 rows: number;
 columns: number;
 spacing: number;
 };

 constraints: {
 maxLength: number;
 maxWidth: number;
 obstacles: Obstacle[];
 };
 };

 results: {
 totalPower: number;
 totalArea: number;
 efficiency: number;
 layout: LayoutPreview;
 };
 };
 };

 benchmark: {
 residential: "3-9 kWc";
 commercial: "36-250 kWc";
 industrial: "250+ kWc";
 };
 };
 };

 typeInstallation: {
 label: "Type d'installation";
 type: "select";
 value: string;
 required: true;

 options: [
 {
 value: "toiture_inclinee";
 label: "Toiture inclinée";
 icon: "home";
 description: "Installation sur toiture existante";

 specifications: {
 inclinaisonMin: 10;
 inclinaisonMax: 60;
 orientationOptimale: 180;

 requirements: [
 "Charpente adaptée",
 "Étanchéité garantie",
 "Accès sécurisé"
 ];
 };

 additionalFields: [
 "inclinaison",
 "orientation",
 "typeFixation",
 "materiauCouverture"
 ];
 },
 {
 value: "toiture_plate";
 label: "Toiture plate";
 icon: "apartment";
 description: "Installation sur toiture terrasse";

 specifications: {
 penteMin: 1;
 penteMax: 5;
 supportRequired: true;

 constraints: [
 "Charge admissible",
 "Évacuation eaux",
 "Accès maintenance"
 ];
 };

 additionalFields: [
 "inclinaisonSupports",
 "typeSupport",
 "lestage",
 "etancheite"
 ];
 },
 {
 value: "ombriere";
 label: "Ombrière parking";
 icon: "directions_car";
 description: "Structure parking photovoltaïque";

 specifications: {
 hauteurMin: 2.5;
 hauteurMax: 4.5;
 porteeMax: 30;

 benefits: [
 "Double usage",
 "Protection véhicules",
 "Rentabilité optimisée"
 ];
 };

 additionalFields: [
 "hauteurLibre",
 "nombrePlaces",
 "typeStructure",
 "fondations"
 ];
 },
 {
 value: "sol";
 label: "Installation au sol";
 icon: "landscape";
 description: "Centrale photovoltaïque au sol";

 specifications: {
 densiteOptimale: 0.8; // MWc/ha
 distanceMin: 4; // m entre rangées
 penteMax: 15; // %

 considerations: [
 "Usage des sols",
 "Raccordement réseau",
 "Maintenance aisée"
 ];
 };

 additionalFields: [
 "surface",
 "typeSol",
 "pente",
 "cloture"
 ];
 },
 {
 value: "agrivoltaique";
 label: "Agrivoltaïque";
 icon: "agriculture";
 description: "Installation compatible agriculture";

 specifications: {
 hauteurMin: 4;
 transparence: 0.7;
 mobilite: true;

 constraints: [
 "Activité agricole maintenue",
 "Espacement adapté",
 "Accès machines"
 ];
 };

 additionalFields: [
 "typeActivite",
 "hauteurStructure",
 "mobilite",
 "transparence"
 ];
 }
 ];

 impact: {
 onCost: {
 multiplier: number;
 additional: number;
 };

 onProduction: {
 factor: number;
 optimization: number;
 };

 onMaintenance: {
 accessibility: number;
 complexity: number;
 };
 };
 };

 localisation: {
 label: "Localisation";
 type: "address";
 value: Address;
 required: true;

 geocoding: {
 provider: "google" | "here" | "nominatim";

 onSelect: (address: Address) => {
 coordinates: [number, number];
 department: string;
 region: string;

 automaticData: {
 irradiation: number;
 temperatureRange: [number, number];
 windZone: string;
 seismicZone: string;
 snowLoad: number;
 };
 };
 };

 mapIntegration: {
 provider: "leaflet" | "mapbox" | "google";

 layers: [
 {
 id: "satellite";
 label: "Vue satellite";
 visible: boolean;
 },
 {
 id: "cadastre";
 label: "Cadastre";
 visible: boolean;
 },
 {
 id: "irradiation";
 label: "Irradiation";
 visible: boolean;

 legend: {
 min: number;
 max: number;
 unit: "kWh/m²/an";
 };
 },
 {
 id: "obstacles";
 label: "Masques";
 visible: boolean;
 editable: boolean;
 }
 ];

 tools: {
 measurement: {
 distance: boolean;
 area: boolean;
 angle: boolean;
 };

 drawing: {
 polygon: boolean;
 rectangle: boolean;
 circle: boolean;
 };

 analysis: {
 shadowAnalysis: boolean;
 suitabilityMap: boolean;
 };
 };
 };

 environmentalData: {
 irradiation: {
 source: "PVGIS" | "Meteonorm" | "SolarGIS";
 annual: number;
 monthly: number[];

 uncertainty: {
 p50: number;
 p90: number;
 method: string;
 };
 };

 temperature: {
 average: number;
 range: [number, number];

 impact: {
 onPerformance: number;
 onDegradation: number;
 };
 };

 wind: {
 averageSpeed: number;
 maxSpeed: number;
 direction: string;

 impact: {
 onCooling: number;
 onLoading: number;
 };
 };
 };
 };
 };
}
```

### Section Technologie et Matériels
```typescript
interface TechnologySection {
 title: " Technologie et matériels";

 panneaux: {
 title: "Modules photovoltaïques";

 selection: {
 method: "library" | "custom";

 fromLibrary: {
 search: {
 query: string;
 filters: {
 brand: string[];
 technology: string[];
 power: { min: number; max: number };
 efficiency: { min: number; max: number };
 certification: string[];
 };
 };

 results: [
 {
 id: string;
 brand: string;
 model: string;

 specifications: {
 power: number;
 efficiency: number;
 voltage: number;
 current: number;

 mechanical: {
 length: number;
 width: number;
 thickness: number;
 weight: number;
 };

 thermal: {
 tempCoeff: number;
 nominalTemp: number;
 maxTemp: number;
 };
 };

 performance: {
 degradation: number;
 warranty: {
 product: number;
 performance: number;
 curve: number[];
 };
 };

 certifications: string[];
 price: number;
 availability: boolean;
 }
 ];
 };

 custom: {
 specifications: {
 puissanceUnitaire: {
 label: "Puissance unitaire";
 type: "number";
 value: number;
 unit: "Wc";

 validation: {
 min: 100;
 max: 800;
 typical: { min: 300, max: 450 };
 };
 };

 rendement: {
 label: "Rendement";
 type: "number";
 value: number;
 unit: "%";

 validation: {
 min: 10;
 max: 25;
 typical: { min: 18, max: 22 };
 };
 };

 technologie: {
 label: "Technologie";
 type: "select";
 value: string;

 options: [
 {
 value: "mono_perc";
 label: "Monocristallin PERC";
 efficiency: { min: 19, max: 22 };
 tempCoeff: -0.35;
 },
 {
 value: "poly";
 label: "Polycristallin";
 efficiency: { min: 15, max: 18 };
 tempCoeff: -0.40;
 },
 {
 value: "bifacial";
 label: "Bifacial";
 efficiency: { min: 20, max: 22 };
 tempCoeff: -0.30;
 bifacialGain: 15;
 },
 {
 value: "thin_film";
 label: "Couches minces";
 efficiency: { min: 10, max: 13 };
 tempCoeff: -0.25;
 }
 ];
 };

 coeffTemp: {
 label: "Coefficient de température";
 type: "number";
 value: number;
 unit: "%/°C";

 presets: [
 { technology: "mono_perc", value: -0.35 },
 { technology: "poly", value: -0.40 },
 { technology: "bifacial", value: -0.30 }
 ];
 };

 degradation: {
 label: "Dégradation annuelle";
 type: "number";
 value: number;
 unit: "%/an";

 presets: [
 { label: "Standard", value: 0.5 },
 { label: "Premium", value: 0.4 },
 { label: "Conservateur", value: 0.7 }
 ];
 };
 };
 };
 };

 arrangement: {
 configuration: {
 nombre: {
 label: "Nombre de modules";
 type: "number";
 value: number;
 calculated: boolean;

 calculation: {
 fromPower: () => number;
 fromArea: () => number;
 optimal: number;
 };
 };

 disposition: {
 label: "Disposition";
 type: "grid";

 layout: {
 rows: number;
 columns: number;
 spacing: {
 horizontal: number;
 vertical: number;
 };

 constraints: {
 maxLength: number;
 maxWidth: number;
 obstacles: Obstacle[];
 };
 };

 preview: {
 show: boolean;
 scale: number;
 exportable: boolean;
 };
 };
 };

 ombrages: {
 label: "Analyse d'ombrages";

 sources: [
 {
 type: "building";
 name: string;
 height: number;
 distance: number;
 angle: number;

 impact: {
 percentage: number;
 periods: TimePeriod[];
 };
 },
 {
 type: "tree";
 name: string;
 height: number;
 distance: number;

 seasonal: {
 winter: number;
 summer: number;
 };
 },
 {
 type: "terrain";
 name: string;
 elevation: number;

 impact: {
 morningShading: number;
 eveningShading: number;
 };
 }
 ];

 analysis: {
 method: "geometric" | "simulation" | "measurement";

 results: {
 totalLoss: number;
 monthlyLoss: number[];
 hourlyMap: number[][];

 visualization: {
 type: "heatmap" | "diagram" | "3d";
 interactive: boolean;
 };
 };
 };
 };
 };
 };

 onduleurs: {
 title: "Onduleurs";

 architecture: {
 type: "string" | "central" | "power_optimizer" | "micro";

 string: {
 label: "Onduleurs de chaîne";

 configuration: {
 nombre: number;
 puissanceUnitaire: number;

 strings: {
 parOnduleur: number;
 modulesParString: number;

 validation: {
 tensionMin: number;
 tensionMax: number;
 courantMax: number;
 };
 };

 monitoring: {
 niveau: "onduleur" | "string" | "module";
 options: string[];
 };
 };
 };

 central: {
 label: "Onduleur central";

 configuration: {
 puissance: number;

 strings: {
 nombre: number;
 modulesParString: number;
 };

 protection: {
 dcDisconnect: boolean;
 acDisconnect: boolean;
 surge: boolean;
 };
 };
 };

 optimizer: {
 label: "Optimiseurs de puissance";

 configuration: {
 onduleur: {
 puissance: number;
 nombre: number;
 };

 optimiseurs: {
 nombre: number;
 puissanceUnitaire: number;

 benefits: {
 shading: number;
 mismatch: number;
 monitoring: boolean;
 };
 };
 };
 };
 };

 dimensionnement: {
 ratioSurdimensionnement: {
 label: "Ratio DC/AC";
 type: "number";
 value: number;

 calculation: {
 dcPower: number;
 acPower: number;
 ratio: number;
 };

 validation: {
 min: 1.0;
 max: 1.5;
 optimal: { min: 1.15, max: 1.30 };

 warnings: {
 underDimensioned: boolean;
 overDimensioned: boolean;
 };
 };

 impact: {
 onProduction: number;
 onClipping: number;
 onEfficiency: number;
 };
 };

 rendement: {
 label: "Rendement onduleur";
 type: "number";
 value: number;
 unit: "%";

 curve: {
 show: boolean;
 data: EfficiencyCurve;

 operating: {
 point: number;
 efficiency: number;
 };
 };

 temperature: {
 derating: number;
 coolingType: "natural" | "forced";
 };
 };
 };

 specifications: {
 entree: {
 tensionMin: number;
 tensionMax: number;
 courantMax: number;

 protection: {
 fusible: boolean;
 parafoudre: boolean;
 };
 };

 sortie: {
 tension: number;
 frequence: number;
 phases: number;

 qualite: {
 thd: number;
 cosPhі: number;
 };
 };

 environnement: {
 temperatureMin: number;
 temperatureMax: number;
 humidite: number;
 altitudeMax: number;

 protection: {
 ip: string;
 ik: string;
 };
 };
 };
 };

 cablage: {
 title: "Câblage et protection";

 dcCabling: {
 label: "Câblage DC";

 strings: {
 longueur: number;
 section: number;

 pertes: {
 resistance: number;
 percentage: number;
 acceptable: boolean;
 };
 };

 protection: {
 fusibles: {
 required: boolean;
 calibre: number;
 };

 parafoudre: {
 type: "type1" | "type2" | "type1+2";
 level: number;
 };

 sectionnement: {
 dcDisconnect: boolean;
 accessible: boolean;
 };
 };
 };

 acCabling: {
 label: "Câblage AC";

 liaison: {
 longueur: number;
 section: number;

 pertes: {
 resistance: number;
 percentage: number;
 acceptable: boolean;
 };
 };

 protection: {
 disjoncteur: {
 calibre: number;
 type: "B" | "C" | "D";
 };

 differentiel: {
 sensibilite: number;
 type: "A" | "AC" | "B";
 };
 };
 };

 mise_a_terre: {
 label: "Mise à la terre";

 systeme: {
 type: "TT" | "TN-S" | "TN-C" | "IT";

 mesures: {
 resistance: number;
 acceptable: boolean;
 };
 };

 masses: {
 panneaux: boolean;
 structures: boolean;
 onduleurs: boolean;
 };
 };
 };
}
```

### Section Estimation de Production
```typescript
interface ProductionEstimationSection {
 title: " Estimation de production";

 methode: {
 label: "Méthode de calcul";
 type: "select";
 value: string;

 options: [
 {
 value: "pvgis";
 label: "PVGIS (Recommandé)";
 description: "Service européen officiel";

 parameters: {
 database: "PVGIS-SARAH" | "PVGIS-NSRDB" | "PVGIS-ERA5";
 period: "2005-2016" | "2005-2020";

 options: {
 tracking: boolean;
 optimal: boolean;
 horizon: boolean;
 };
 };
 },
 {
 value: "meteonorm";
 label: "Meteonorm";
 description: "Base de données météo mondiale";

 parameters: {
 version: "8.0" | "7.3";
 period: "2000-2019";

 options: {
 tmy: boolean;
 p50: boolean;
 p90: boolean;
 };
 };
 },
 {
 value: "manuel";
 label: "Saisie manuelle";
 description: "Données personnalisées";

 parameters: {
 irradiation: number;
 temperature: number;
 source: string;
 };
 }
 ];
 };

 donnees_site: {
 label: "Données du site";

 irradiation: {
 annuelle: {
 label: "Irradiation annuelle";
 value: number;
 unit: "kWh/m²/an";
 source: string;

 validation: {
 min: 800;
 max: 2000;
 typical: { min: 1100, max: 1600 };
 };
 };

 mensuelle: {
 label: "Répartition mensuelle";
 data: number[];

 visualization: {
 type: "bar" | "line";
 showAverage: boolean;

 comparison: {
 withTypical: boolean;
 withOptimal: boolean;
 };
 };
 };

 incertitude: {
 label: "Incertitude";

 p50: number;
 p75: number;
 p90: number;

 sources: [
 "Variabilité interannuelle",
 "Incertitude mesure",
 "Méthode d'interpolation"
 ];
 };
 };

 temperature: {
 moyenne: {
 label: "Température moyenne";
 value: number;
 unit: "°C";

 impact: {
 onPerformance: number;
 coefficient: number;
 };
 };

 mensuelle: {
 label: "Températures mensuelles";
 data: number[];

 extremes: {
 min: number;
 max: number;

 impact: {
 onDegradation: number;
 onLifespan: number;
 };
 };
 };
 };

 autres: {
 vent: {
 label: "Vitesse du vent";
 value: number;
 unit: "m/s";

 impact: {
 onCooling: number;
 onPerformance: number;
 };
 };

 humidite: {
 label: "Humidité relative";
 value: number;
 unit: "%";

 impact: {
 onCorrosion: number;
 onDegradation: number;
 };
 };
 };
 };

 parametres_performance: {
 label: "Paramètres de performance";

 ratioPerformance: {
 label: "Ratio de performance global";
 type: "number";
 value: number;
 unit: "%";

 calculation: {
 auto: boolean;

 composants: {
 temperature: {
 label: "Température";
 value: number;
 unit: "%";

 calculation: {
 tempModule: number;
 tempAmbient: number;
 tempCoeff: number;

 formula: string;
 };
 };

 salissure: {
 label: "Salissure";
 value: number;
 unit: "%";

 factors: {
 environment: string;
 cleaningFreq: number;
 seasonality: number[];
 };
 };

 ombrages: {
 label: "Ombrages";
 value: number;
 unit: "%";

 sources: ShadingSource[];
 };

 mismatch: {
 label: "Mismatch";
 value: number;
 unit: "%";

 causes: [
 "Tolérance modules",
 "Différences vieillissement",
 "Conditions non-uniformes"
 ];
 };

 onduleur: {
 label: "Onduleur";
 value: number;
 unit: "%";

 curve: EfficiencyCurve;
 };

 cables: {
 label: "Câbles";
 value: number;
 unit: "%";

 calculation: {
 dcLosses: number;
 acLosses: number;
 total: number;
 };
 };

 disponibilite: {
 label: "Disponibilité";
 value: number;
 unit: "%";

 factors: {
 maintenance: number;
 defaillances: number;
 reseau: number;
 };
 };
 };

 total: {
 calculated: number;
 manual: number;

 comparison: {
 typical: { min: 75, max: 85 };
 excellent: { min: 85, max: 90 };
 };
 };
 };
 };

 degradation: {
 label: "Dégradation";

 annuelle: {
 label: "Dégradation annuelle";
 value: number;
 unit: "%/an";

 presets: [
 { label: "Standard", value: 0.5 },
 { label: "Premium", value: 0.4 },
 { label: "Conservateur", value: 0.7 }
 ];
 };

 evolution: {
 label: "Évolution sur 25 ans";

 data: {
 years: number[];
 performance: number[];

 warranty: {
 linear: boolean;
 guarantee: number; // % à 25 ans
 };
 };

 visualization: {
 type: "line";
 showWarranty: boolean;
 exportable: boolean;
 };
 };
 };
 };

 resultats: {
 label: "Résultats de production";

 production: {
 annuelle: {
 label: "Production annuelle";
 value: number;
 unit: "MWh/an";

 breakdown: {
 par_mois: number[];
 par_saison: SeasonalProduction;

 visualization: {
 type: "bar" | "line" | "heatmap";
 showTrend: boolean;
 interactive: boolean;
 };
 };
 };

 specifique: {
 label: "Production spécifique";
 value: number;
 unit: "kWh/kWc/an";

 benchmark: {
 france: { min: 900, max: 1400 };
 region: { min: number; max: number };

 comparison: {
 percentile: number;
 category: "low" | "average" | "high";
 };
 };
 };

 facteur_charge: {
 label: "Facteur de charge";
 value: number;
 unit: "%";

 calculation: {
 productionAnnuelle: number;
 productionTheorique: number;

 comparison: {
 typical: { min: 10, max: 16 };
 excellent: { min: 16, max: 20 };
 };
 };
 };
 };

 evolution: {
 label: "Évolution temporelle";

 sur25ans: {
 production: number[];
 cumul: number[];

 scenarios: {
 optimiste: ProductionScenario;
 probable: ProductionScenario;
 pessimiste: ProductionScenario;
 };

 visualization: {
 type: "line" | "area";
 showScenarios: boolean;
 confidence: boolean;
 };
 };
 };

 incertitudes: {
 label: "Analyse d'incertitude";

 sources: [
 {
 name: "Variabilité météo";
 impact: number;
 type: "aleatory";
 },
 {
 name: "Modèle de calcul";
 impact: number;
 type: "epistemic";
 },
 {
 name: "Dégradation";
 impact: number;
 type: "aleatory";
 }
 ];

 resultats: {
 p50: number;
 p75: number;
 p90: number;

 distribution: {
 type: "normal" | "lognormal" | "beta";
 parameters: number[];
 };
 };
 };
 };
}
```

## État et données

```typescript
interface ProjectTechnicalState {
 // Configuration générale
 general: {
 power: number;
 installationType: string;
 location: Address;
 coordinates: [number, number];
 };

 // Configuration technique
 technical: {
 panels: {
 selection: PanelSelection;
 specifications: PanelSpecs;
 arrangement: PanelArrangement;
 };

 inverters: {
 architecture: InverterArchitecture;
 specifications: InverterSpecs;
 sizing: InverterSizing;
 };

 cabling: {
 dc: DCCabling;
 ac: ACCabling;
 protection: Protection;
 };
 };

 // Données environnementales
 environmental: {
 irradiation: {
 source: string;
 annual: number;
 monthly: number[];
 uncertainty: UncertaintyData;
 };

 temperature: {
 average: number;
 monthly: number[];
 extremes: [number, number];
 };

 other: {
 wind: number;
 humidity: number;
 };
 };

 // Calculs de production
 production: {
 method: string;
 parameters: ProductionParameters;

 results: {
 annual: number;
 specific: number;
 monthly: number[];

 factors: {
 pr: number;
 degradation: number;
 uncertainty: UncertaintyResults;
 };
 };

 evolution: {
 years: number[];
 production: number[];
 scenarios: ProductionScenarios;
 };
 };

 // Validation et warnings
 validation: {
 general: ValidationResult;
 technical: ValidationResult;
 production: ValidationResult;

 warnings: Warning[];
 errors: Error[];
 };

 // État UI
 ui: {
 activeSection: string;
 calculatingProduction: boolean;
 showAdvanced: boolean;

 maps: {
 visible: boolean;
 activeLayer: string;
 tools: MapTools;
 };

 charts: {
 productionChart: ChartConfig;
 temperatureChart: ChartConfig;
 degradationChart: ChartConfig;
 };
 };
}
```

## API Endpoints

```typescript
// Données météo/irradiation
GET /api/weather/pvgis
Query: {
 lat: number;
 lon: number;
 slope: number;
 aspect: number;
 database: string;
}

// Bibliothèque modules PV
GET /api/panels/library
Query: {
 search?: string;
 brand?: string;
 technology?: string;
 power?: string;
}

// Calcul de production
POST /api/calculations/production
Body: {
 location: [number, number];
 panels: PanelConfig;
 inverters: InverterConfig;
 environmental: EnvironmentalData;
}

// Analyse d'ombrages
POST /api/analysis/shading
Body: {
 location: [number, number];
 installation: InstallationConfig;
 obstacles: Obstacle[];
}

// Validation configuration
POST /api/validation/technical
Body: {
 configuration: TechnicalConfig;
}
```

## Exemple d'implémentation

```tsx
import React, { useState, useEffect } from 'react';
import {
 ProjectTechnicalLayout,
 InstallationConfig,
 TechnologyConfig,
 ProductionEstimation,
 ValidationSummary
} from '@/components/technical';

export const ProjectTechnicalPage: React.FC = () => {
 const [config, setConfig] = useState<TechnicalConfig>();
 const [production, setProduction] = useState<ProductionResults>();
 const [validation, setValidation] = useState<ValidationState>();

 // Calcul automatique de production
 useEffect(() => {
 if (config?.general?.power && config?.general?.location) {
 calculateProduction();
 }
 }, [config?.general, config?.technical]);

 const calculateProduction = async () => {
 try {
 const results = await productionAPI.calculate({
 location: config.general.coordinates,
 panels: config.technical.panels,
 inverters: config.technical.inverters,
 environmental: config.environmental
 });

 setProduction(results);
 } catch (error) {
 console.error('Erreur calcul production:', error);
 }
 };

 const handleConfigChange = (section: string, field: string, value: any) => {
 setConfig(prev => ({
...prev,
 [section]: {
...prev[section],
 [field]: value
 }
 }));

 // Validation temps réel
 validateConfiguration(section, field, value);
 };

 return (
 <ProjectTechnicalLayout>
 <ValidationSummary
 validation={validation}
 onSectionClick={scrollToSection}
 />

 <InstallationConfig
 config={config?.general}
 onChange={(field, value) =>
 handleConfigChange('general', field, value)
 }
 validation={validation?.general}
 />

 <TechnologyConfig
 config={config?.technical}
 onChange={(field, value) =>
 handleConfigChange('technical', field, value)
 }
 validation={validation?.technical}
 />

 <ProductionEstimation
 config={config}
 results={production}
 onChange={(field, value) =>
 handleConfigChange('production', field, value)
 }
 onRecalculate={calculateProduction}
 />
 </ProjectTechnicalLayout>
 );
};
```

Cette configuration technique permet une définition complète et précise du projet photovoltaïque avec calculs de production automatiques et validation en temps réel.