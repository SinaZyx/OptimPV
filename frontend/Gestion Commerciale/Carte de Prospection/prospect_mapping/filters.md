# Filtres et Recherche - Module Prospect Mapping

## Vue d'ensemble

Les filtres de la carte de prospection permettent de affiner les données Enedis selon des critères de consommation énergétique et de caractéristiques de bâtiments. Interface simple et efficace basée sur les données réelles du département 06.

## Structure de filtrage

### Filtres principaux (Logique OptimPV)
```typescript
interface MainFilters {
 title: " Filtres de Prospection";
 layout: "2_columns";

 consumptionFilter: {
 column: 1;
 label: "Consommation annuelle (kWh)";
 type: "range_slider";

 dataSource: {
 field: "consommation_kwh";
 calculation: {
 min: "data['consommation_kwh'].min()";
 max: "data['consommation_kwh'].max()";
 mean: "data['consommation_kwh'].mean()";
 };
 };

 slider: {
 min: "int(min_consumption)";
 max: "int(max_consumption)";
 value: "[int(min_consumption), int(max_consumption)]";
 step: 1000;
 format: "%d kWh";
 labelVisibility: "collapsed";
 };

 caption: {
 display: "De {consumption_range[0]:,} à {consumption_range[1]:,} kWh/an";
 dynamic: true;
 };

 filterLogic: """
 filtered_data = filtered_data[
 (filtered_data['consommation_kwh'] >= consumption_range[0]) &
 (filtered_data['consommation_kwh'] <= consumption_range[1])
 ]
 """;
 };

 housingFilter: {
 column: 2;
 label: "Nombre de logements";
 type: "range_slider";
 visible: "'nombre_de_logements' in data.columns";

 dataSource: {
 field: "nombre_de_logements";
 calculation: {
 min: "int(data['nombre_de_logements'].min())";
 max: "int(data['nombre_de_logements'].max())";
 };
 };

 slider: {
 min: "min_logements";
 max: "max_logements";
 value: "[min_logements, max_logements]";
 step: 1;
 labelVisibility: "collapsed";
 };

 caption: {
 display: "De {logements_range[0]} à {logements_range[1]} logements";
 dynamic: true;
 };

 filterLogic: """
 if logements_range and 'nombre_de_logements' in filtered_data.columns:
 filtered_data = filtered_data[
 (filtered_data['nombre_de_logements'] >= logements_range[0]) &
 (filtered_data['nombre_de_logements'] <= logements_range[1])
 ]
 """;
 };
}
```

### Filtre par Seuil de Consommation (Logique historique)
```typescript
interface ThresholdFilter {
 purpose: "Filtrage simple par seuil de consommation";
 deprecated: false; // Toujours utilisé en interne

 function: "filter_data_by_consumption";
 params: {
 data: "DataFrame";
 threshold: "number"; // En kWh
 };

 defaultThreshold: {
 source: "mean_consumption";
 calculation: "data['consommation_kwh'].mean()";
 fallback: 7000; // kWh
 };

 implementation: """
 def filter_data_by_consumption(data: pd.DataFrame, threshold: float) -> pd.DataFrame:
 return data[data['consommation_kwh'] >= threshold]
 """;

 usage: "Utilisé pour établir un seuil minimum de consommation avant affichage détaillé";
}
```

### Filtre par Communes
```typescript
interface CommuneFilter {
 purpose: "Filtrage géographique par communes sélectionnées";

 function: "filter_data_by_communes";
 params: {
 data: "DataFrame";
 communes: "string[]";
 };

 dataSource: {
 field: "nom_commune";
 unique: "data['nom_commune'].unique()";
 };

 modes: [
 {
 id: "proximity_mougins";
 communes: "get_closest_communes_to_mougins()";
 description: "10 communes les plus proches de Mougins";
 estimatedCount: 2000;
 },
 {
 id: "custom_selection";
 communes: "user_selected_communes";
 description: "Communes sélectionnées manuellement";
 estimatedCount: "len(communes) * 200";
 },
 {
 id: "all_communes";
 communes: "null"; // Pas de filtre
 description: "Toutes les communes du département 06";
 estimatedCount: 10000;
 }
 ];

 implementation: """
 def filter_data_by_communes(data: pd.DataFrame, communes: List[str]) -> pd.DataFrame:
 if not communes:
 return data
 return data[data['nom_commune'].isin(communes)]
 """;

 usage: "Appliqué automatiquement selon le mode de chargement sélectionné";
}
```

## Logique de filtrage temps réel

### Pipeline de Filtrage
```typescript
interface FilteringPipeline {
 order: [
 "load_base_data",
 "apply_commune_filter",
 "apply_consumption_threshold",
 "apply_range_filters",
 "update_statistics"
 ];

 steps: {
 loadBaseData: {
 function: "load_and_process_data";
 params: {
 communes_filter: "string[] | null";
 proximity_mode: "boolean";
 };
 cache: {
 enabled: true;
 ttl: 3600; // 1 heure
 };
 };

 applyCommuneFilter: {
 condition: "selected_communes.length > 0";
 function: "filter_data_by_communes";
 params: {
 data: "base_data";
 communes: "selected_communes";
 };
 };

 applyConsumptionThreshold: {
 function: "filter_data_by_consumption";
 params: {
 data: "commune_filtered_data";
 threshold: "consumption_threshold";
 };
 default: {
 threshold: "mean_consumption";
 };
 };

 applyRangeFilters: {
 consumptionRange: """
 filtered_data = filtered_data[
 (filtered_data['consommation_kwh'] >= consumption_range[0]) &
 (filtered_data['consommation_kwh'] <= consumption_range[1])
 ]
 """;

 housingRange: """
 if logements_range and 'nombre_de_logements' in filtered_data.columns:
 filtered_data = filtered_data[
 (filtered_data['nombre_de_logements'] >= logements_range[0]) &
 (filtered_data['nombre_de_logements'] <= logements_range[1])
 ]
 """;
 };

 updateStatistics: {
 realTimeStats: [
 "total_points",
 "average_consumption",
 "total_consumption",
 "communes_displayed",
 "precision_quality"
 ];

 calculation: """
 stats = {
 'total_points': len(filtered_data),
 'average_consumption': filtered_data['consommation_kwh'].mean() if len(filtered_data) > 0 else 0,
 'total_consumption': filtered_data['consommation_kwh'].sum() / 1000, // MWh
 'communes_displayed': filtered_data['nom_commune'].nunique() if len(filtered_data) > 0 else 0,
 'precision_quality': calculate_precision_quality(filtered_data)
 }
 """;
 };
 };
}
```

### Gestion des Valeurs par Défaut
```typescript
interface DefaultValues {
 consumptionFilter: {
 initialization: """
 min_consumption = data['consommation_kwh'].min()
 max_consumption = data['consommation_kwh'].max()
 mean_consumption = data['consommation_kwh'].mean()
 consumption_threshold = mean_consumption
 """;

 rangeSlider: {
 min: "int(min_consumption)";
 max: "int(max_consumption)";
 defaultValue: "[int(min_consumption), int(max_consumption)]";
 step: 1000;
 };
 };

 housingFilter: {
 condition: "'nombre_de_logements' in data.columns";
 initialization: """
 if 'nombre_de_logements' in data.columns:
 min_logements = int(data['nombre_de_logements'].min())
 max_logements = int(data['nombre_de_logements'].max())
 logements_range = (min_logements, max_logements)
 else:
 logements_range = None
 """;

 rangeSlider: {
 min: "min_logements";
 max: "max_logements";
 defaultValue: "[min_logements, max_logements]";
 step: 1;
 };
 };

 communes: {
 selectedCommunes: "[]"; // Vide par défaut
 proximityMode: "true"; // Mode Mougins par défaut
 };
}
```

## Interface des filtres

### Composants UI
```typescript
interface FilterComponents {
 consumptionRangeSlider: {
 component: "st.slider";
 label: "Plage de consommation";
 params: {
 min_value: "int(min_consumption)";
 max_value: "int(max_consumption)";
 value: "(int(min_consumption), int(max_consumption))";
 step: 1000;
 format: "%d kWh";
 label_visibility: "collapsed";
 };

 caption: {
 component: "st.caption";
 content: "f'De {consumption_range[0]:,} à {consumption_range[1]:,} kWh/an'";
 };
 };

 housingRangeSlider: {
 component: "st.slider";
 condition: "'nombre_de_logements' in data.columns";
 label: "Nombre de logements";
 params: {
 min_value: "min_logements";
 max_value: "max_logements";
 value: "(min_logements, max_logements)";
 step: 1;
 label_visibility: "collapsed";
 };

 caption: {
 component: "st.caption";
 content: "f'De {logements_range[0]} à {logements_range[1]} logements'";
 };
 };

 layout: {
 columns: "st.columns(2)";
 responsiveBreakdown: {
 desktop: "2_columns";
 tablet: "1_column";
 mobile: "1_column";
 };
 };
}
```

### Validation des Filtres
```typescript
interface FilterValidation {
 consumptionRange: {
 dataType: "tuple[int, int]";
 validation: {
 min: "consumption_range[0] >= 0";
 max: "consumption_range[1] <= data['consommation_kwh'].max()";
 order: "consumption_range[0] <= consumption_range[1]";
 };

 errorHandling: {
 invalidRange: "Ajuster automatiquement à la plage valide";
 emptyData: "Masquer le filtre si aucune donnée";
 };
 };

 housingRange: {
 dataType: "tuple[int, int] | None";
 validation: {
 columnExists: "'nombre_de_logements' in data.columns";
 min: "logements_range[0] >= 0";
 max: "logements_range[1] <= data['nombre_de_logements'].max()";
 order: "logements_range[0] <= logements_range[1]";
 };

 errorHandling: {
 missingColumn: "Masquer le filtre";
 invalidRange: "Ajuster automatiquement";
 };
 };

 communes: {
 dataType: "list[str]";
 validation: {
 existingCommunes: "all(commune in get_all_communes_dept_06() for commune in selected_communes)";
 department: "Limité au département 06";
 };

 errorHandling: {
 invalidCommunes: "Filtrer les communes inexistantes";
 emptySelection: "Revenir au mode proximité Mougins";
 };
 };
}
```

## Performance et Optimisation

### Gestion du Cache de Filtrage
```typescript
interface FilterCaching {
 dataCache: {
 baseData: {
 key: "load_and_process_data";
 ttl: 3600; // 1 heure
 invalidation: "manual"; // Bouton refresh
 };

 filteredResults: {
 key: "session_state";
 scope: "session";
 persistence: false;
 };
 };

 computationOptimization: {
 lazyEvaluation: {
 enabled: true;
 trigger: "filter_change";
 debounceMs: 300;
 };

 memoryManagement: {
 maxDataPoints: 50000;
 chunkSize: 10000;
 virtualScroll: true;
 };
 };

 responsiveFiltering: {
 realTime: {
 enabled: true;
 updateTrigger: "slider_change";
 statisticsUpdate: "immediate";
 };

 batchProcessing: {
 enabled: false; // Simple filtering logic
 batchSize: 1000;
 };
 };
}
```

### Indicateurs de Performance
```typescript
interface PerformanceIndicators {
 filteringSpeed: {
 measurement: "time_to_filter";
 targets: {
 small: "<100ms"; // <1000 points
 medium: "<500ms"; // 1000-10000 points
 large: "<2s"; // >10000 points
 };
 };

 memoryUsage: {
 measurement: "dataframe_memory";
 targets: {
 baseData: "<100MB";
 filteredData: "<50MB";
 sessionState: "<10MB";
 };
 };

 userExperience: {
 responseTime: "<200ms"; // Slider response
 statisticsUpdate: "<100ms"; // Metrics recalculation
 mapUpdate: "<1s"; // Map redraw
 };
}
```

## Fonctions de filtrage intégrées

### Fonctions Core Data Handler
```typescript
interface CoreFilterFunctions {
 filter_data_by_consumption: {
 signature: "(data: pd.DataFrame, threshold: float) -> pd.DataFrame";
 purpose: "Filtre les données par seuil minimum de consommation";
 implementation: "return data[data['consommation_kwh'] >= threshold]";
 usage: "Filtrage préliminaire avant affichage";
 };

 filter_data_by_communes: {
 signature: "(data: pd.DataFrame, communes: List[str]) -> pd.DataFrame";
 purpose: "Filtre les données par liste de communes";
 implementation: """
 if not communes:
 return data
 return data[data['nom_commune'].isin(communes)]
 """;
 usage: "Filtrage géographique par sélection de communes";
 };

 get_unique_communes: {
 signature: "(data: pd.DataFrame) -> List[str]";
 purpose: "Récupère la liste unique des communes dans les données";
 implementation: "return sorted(data['nom_commune'].unique().tolist())";
 usage: "Alimentation des filtres de sélection de communes";
 };

 get_all_communes_dept_06: {
 signature: "() -> List[str]";
 purpose: "Récupère toutes les communes du département 06";
 apiCall: "https://geo.api.gouv.fr/communes?codeDepartement=06";
 cache: {
 enabled: true;
 ttl: 86400; // 24 heures
 };
 usage: "Sélection personnalisée de communes";
 };

 get_closest_communes_to_mougins: {
 signature: "() -> List[str]";
 purpose: "Récupère les 10 communes les plus proches de Mougins";
 implementation: """
 mougins_center = (43.5974, 7.0058)
 # Calcul des distances et tri
 return sorted_communes[:10]
 """;
 usage: "Mode proximité Mougins (recommandé)";
 };
}
```

### Fonctions utilitaires de filtrage
```typescript
interface UtilityFunctions {
 calculate_filter_statistics: {
 purpose: "Calcule les statistiques après filtrage";
 params: {
 originalData: "pd.DataFrame";
 filteredData: "pd.DataFrame";
 };
 returns: {
 totalOriginal: "int";
 totalFiltered: "int";
 reductionPercentage: "float";
 averageConsumption: "float";
 totalConsumption: "float";
 uniqueCommunes: "int";
 };
 };

 validate_filter_ranges: {
 purpose: "Valide les plages de filtres avant application";
 params: {
 data: "pd.DataFrame";
 consumptionRange: "tuple[int, int]";
 housingRange: "tuple[int, int] | None";
 };
 returns: {
 valid: "bool";
 errors: "List[str]";
 adjustedRanges: "dict";
 };
 };

 optimize_filter_performance: {
 purpose: "Optimise les performances de filtrage pour gros datasets";
 params: {
 data: "pd.DataFrame";
 chunkSize: "int";
 };
 implementation: {
 chunking: "Divise les données en chunks pour traitement";
 indexing: "Utilise les index pandas pour accélération";
 memory: "Libère la mémoire des chunks traités";
 };
 };
}
```

## Interface utilisateur responsive

### Adaptation Mobile
```typescript
interface ResponsiveFilters {
 breakpoints: {
 desktop: ">1200px";
 tablet: "768px-1200px";
 mobile: "<768px";
 };

 layoutAdaptation: {
 desktop: {
 layout: "2_columns";
 sliderWidth: "full";
 captionPosition: "below";
 };

 tablet: {
 layout: "2_columns";
 sliderWidth: "full";
 captionPosition: "below";
 };

 mobile: {
 layout: "1_column";
 sliderWidth: "full";
 captionPosition: "inline";
 stackOrder: ["consumption", "housing"];
 };
 };

 interactionOptimization: {
 touchTargets: {
 sliderHandle: "44px min";
 buttons: "48px min";
 };

 gestureSupport: {
 pinchZoom: false; // On sliders
 swipeNavigation: false;
 tapToSelect: true;
 };
 };
}
```

## Cas d'usage typiques

### Scénarios de filtrage
```typescript
interface FilteringScenarios {
 highConsumptionProspects: {
 description: "Prospects à forte consommation (>15000 kWh/an)";
 filters: {
 consumptionRange: "[15000, 100000]";
 housingRange: null;
 communes: "proximity_mougins";
 };
 expectedResults: "~200-500 prospects";
 use_case: "Cibles prioritaires pour installations importantes";
 };

 collectiveHousing: {
 description: "Immeubles collectifs (>5 logements)";
 filters: {
 consumptionRange: "[10000, 50000]";
 housingRange: "[5, 100]";
 communes: "custom_selection";
 };
 expectedResults: "~100-300 prospects";
 use_case: "Projets collectifs et copropriétés";
 };

 individualHouses: {
 description: "Maisons individuelles";
 filters: {
 consumptionRange: "[8000, 20000]";
 housingRange: "[1, 2]";
 communes: "all_communes";
 };
 expectedResults: "~2000-5000 prospects";
 use_case: "Marché résidentiel individuel";
 };

 businessTargets: {
 description: "Cibles professionnelles (forte consommation)";
 filters: {
 consumptionRange: "[30000, 500000]";
 housingRange: null;
 communes: "cannes_antibes_nice";
 };
 expectedResults: "~50-200 prospects";
 use_case: "Secteur tertiaire et industriel";
 };
}
```

## Configuration technique

- **Framework de filtrage**: Pandas DataFrame operations
- **Interface utilisateur**: Streamlit native components (st.slider, st.selectbox)
- **Validation**: Python type hints + runtime checks
- **Performance**: Index-based filtering + chunking pour gros datasets
- **Cache**: Session state Streamlit + decorateurs @st.cache_data
- **Responsive**: CSS Grid + Streamlit column layout