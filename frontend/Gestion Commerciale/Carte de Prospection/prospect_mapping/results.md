# Résultats et Statistiques - Module Prospect Mapping

## Vue d'ensemble

Le système de statistiques temps réel d'OptimPV affiche les métriques clés des données Enedis filtrées avec indicateurs de qualité, légende interactive et résumés statistiques détaillés pour la prospection solaire.

## Structure des résultats

### Statistiques Temps Réel (5 Colonnes)
```typescript
interface RealTimeStatistics {
 layout: "5_columns_equal";
 title: "Métriques de Prospection";
 updateTrigger: "filter_change";

 columns: [
 {
 id: "total_points";
 label: "Total Points";
 calculation: "len(filtered_data)";
 format: "{value:,}";

 delta: {
 enabled: true;
 calculation: "len(filtered_data) - len(data)";
 condition: "len(filtered_data)!= len(data)";
 format: "{delta:,}";
 color: "auto"; // green if positive, red if negative
 };

 tooltip: "Nombre total de bâtiments après filtrage";
 },
 {
 id: "average_consumption";
 label: "Consommation Moyenne";
 unit: "kWh";

 calculation: """
 if len(filtered_data) > 0:
 avg_consumption = filtered_data['consommation_kwh'].mean()
 return f"{avg_consumption:,.0f} kWh"
 else:
 return "N/A"
 """;

 fallback: "N/A";
 tooltip: "Consommation énergétique moyenne des bâtiments sélectionnés";
 },
 {
 id: "total_consumption";
 label: "Consommation Totale";
 unit: "MWh";

 calculation: """
 if len(filtered_data) > 0:
 total_consumption = filtered_data['consommation_kwh'].sum()
 return f"{total_consumption/1000:,.0f} MWh"
 else:
 return "N/A"
 """;

 fallback: "N/A";
 tooltip: "Consommation énergétique totale (conversion automatique kWh → MWh)";
 },
 {
 id: "communes_count";
 label: "Communes Affichées" | "Communes Sélectionnées";

 calculation: """
 if selected_communes:
 return len(selected_communes)
 else:
 unique_communes = filtered_data['nom_commune'].nunique() if len(filtered_data) > 0 else 0
 return unique_communes
 """;

 labelLogic: {
 condition: "selected_communes";
 ifTrue: "Communes Sélectionnées";
 ifFalse: "Communes Affichées";
 };

 tooltip: "Nombre de communes dans la sélection actuelle";
 },
 {
 id: "precision_quality";
 label: " Précision";
 type: "quality_indicator";

 calculation: {
 dataQuality: """
 if len(filtered_data) > 0 and 'location_confidence' in filtered_data.columns:
 high_precision = (filtered_data['location_confidence'] == 'high').sum()
 osm_precision = (filtered_data['data_source'] == 'OSM').sum()
 total_points = len(filtered_data)

 quality_points = high_precision + osm_precision
 precision_rate = (quality_points / total_points * 100) if total_points > 0 else 0

 return {
 'rate': precision_rate,
 'quality_points': quality_points,
 'total_points': total_points
 }
 else:
 return {'rate': 0, 'quality_points': 0, 'total_points': 0}
 """;

 statusMapping: {
 thresholds: [
 { min: 30, status: "Bonne", icon: "" },
 { min: 10, status: "Moyenne", icon: "" },
 { min: 0, status: "Basique", icon: "" }
 ];

 default: { status: "Analyse...", icon: "" };
 };
 };

 display: {
 mainValue: "status"; // "Bonne", "Moyenne", "Basique"
 delta: "{icon} {quality_points}/{total_points}";
 tooltip: "Qualité des données géographiques basée sur BD TOPO et OSM";
 };
 }
 ];
}
```

### Légende Compacte (4 Métriques)
```typescript
interface CompactLegend {
 title: "Légende des Données";
 layout: "4_columns_equal";
 dependsOn: "filtered_data";

 dataSource: {
 function: "get_map_legend_info";
 params: "filtered_data";
 returns: {
 min_consumption: "number";
 mean_consumption: "number";
 max_consumption: "number";
 total_points: "number";
 };
 };

 metrics: [
 {
 id: "min_value";
 icon: "";
 label: "Min";
 value: "legend_info['min_consumption']";
 format: "{value:,.0f} kWh";
 color: "#22c55e"; // Green
 description: "Consommation minimale dans la sélection";
 },
 {
 id: "mean_value";
 icon: "";
 label: "Moyenne";
 value: "legend_info['mean_consumption']";
 format: "{value:,.0f} kWh";
 color: "#f59e0b"; // Orange/Yellow
 description: "Consommation moyenne dans la sélection";
 },
 {
 id: "max_value";
 icon: "";
 label: "Max";
 value: "legend_info['max_consumption']";
 format: "{value:,.0f} kWh";
 color: "#ef4444"; // Red
 description: "Consommation maximale dans la sélection";
 },
 {
 id: "point_count";
 icon: "";
 label: "Points";
 value: "len(filtered_data)";
 format: "{value:,}";
 color: "#3b82f6"; // Blue
 description: "Nombre total de points sur la carte";
 }
 ];

 conditionalDisplay: {
 condition: "len(filtered_data) > 0";
 fallback: {
 message: " Aucune donnée ne correspond aux filtres sélectionnés.";
 suggestion: " Essayez de réduire le seuil de consommation ou de sélectionner d'autres communes.";
 };
 };
}
```

## Résumés Statistiques Détaillés

### Statistiques de Consommation
```typescript
interface ConsumptionStatistics {
 title: " Résumé Statistique";
 trigger: "Générer Résumé Statistique"; // Button

 function: "_show_statistics_summary";
 params: "filtered_data: pd.DataFrame";

 layout: "2_columns";

 leftColumn: {
 title: "Statistiques de Consommation (kWh)";

 calculation: """
 consumption_stats = data['consommation_kwh'].describe()

 stats_df = pd.DataFrame({
 'Métrique': ['Minimum', 'Maximum', 'Moyenne', 'Médiane', 'Écart-type'],
 'Valeur': [
 f"{consumption_stats['min']:,.0f}",
 f"{consumption_stats['max']:,.0f}",
 f"{consumption_stats['mean']:,.0f}",
 f"{consumption_stats['50%']:,.0f}",
 f"{consumption_stats['std']:,.0f}"
 ]
 })
 """;

 display: {
 component: "st.dataframe";
 params: {
 data: "stats_df";
 hide_index: true;
 use_container_width: true;
 };
 };
 };

 rightColumn: {
 title: "Top 10 Communes par Nombre de Prospects";
 condition: "'nom_commune' in data.columns";

 calculation: """
 top_communes = data['nom_commune'].value_counts().head(10)
 communes_df = pd.DataFrame({
 'Commune': top_communes.index,
 'Nombre de Prospects': top_communes.values
 })
 """;

 display: {
 component: "st.dataframe";
 params: {
 data: "communes_df";
 hide_index: true;
 use_container_width: true;
 };
 };
 };
}
```

### Répartition par Tranches de Consommation
```typescript
interface ConsumptionDistribution {
 title: "Répartition par Tranche de Consommation";

 binning: {
 bins: [0, 5000, 10000, 15000, 20000, "float('inf')"];
 labels: ['0-5k kWh', '5-10k kWh', '10-15k kWh', '15-20k kWh', '20k+ kWh'];

 calculation: """
 data['tranche_conso'] = pd.cut(
 data['consommation_kwh'],
 bins=bins,
 labels=labels,
 right=False
 )
 distribution = data['tranche_conso'].value_counts().sort_index()
 """;
 };

 output: {
 calculation: """
 distribution_df = pd.DataFrame({
 'Tranche': distribution.index,
 'Nombre': distribution.values,
 'Pourcentage': (distribution.values / len(data) * 100).round(1)
 })
 """;

 display: {
 component: "st.dataframe";
 params: {
 data: "distribution_df";
 hide_index: true;
 use_container_width: true;
 };
 };
 };

 insights: {
 enabled: true;
 calculations: [
 {
 metric: "most_common_range";
 calculation: "distribution.idxmax()";
 description: "Tranche de consommation la plus fréquente";
 },
 {
 metric: "high_consumption_rate";
 calculation: "(data['consommation_kwh'] > 15000).mean() * 100";
 description: "Pourcentage de prospects à forte consommation (>15k kWh)";
 format: "{value:.1f}%";
 }
 ];
 };
}
```

## Gestion des Données et Export

### Export des Données Filtrées
```typescript
interface DataExport {
 title: " Export des Données";
 condition: "len(filtered_data) > 0";
 layout: "2_columns";

 leftColumn: {
 exportCSV: {
 component: "st.download_button";
 label: "Télécharger en CSV";

 dataPreparation: """
 csv_data = filtered_data.to_csv(index=False).encode('utf-8')
 """;

 params: {
 data: "csv_data";
 file_name: "f'prospects_dept06_{len(filtered_data)}_points.csv'";
 mime: "text/csv";
 help: "Télécharge les données filtrées au format CSV";
 use_container_width: true;
 };
 };
 };

 rightColumn: {
 generateSummary: {
 component: "st.button";
 label: "Générer Résumé Statistique";
 onClick: "_show_statistics_summary(filtered_data)";
 use_container_width: true;
 };
 };

 fileNaming: {
 pattern: "prospects_dept06_{count}_points.csv";
 timestamping: false; // Simplified naming
 userFriendly: true;
 };
}
```

### Gestion des Sessions et Cache
```typescript
interface SessionDataManagement {
 sessionState: {
 mainData: {
 key: "data";
 type: "pd.DataFrame";
 persistence: "session";
 size_limit: "100MB";
 };

 filteredData: {
 key: "filtered_data";
 type: "pd.DataFrame";
 persistence: "session";
 derived_from: "data";
 };

 selectedParcel: {
 key: "selected_parcel_index";
 type: "int | None";
 persistence: "session";
 default: null;
 };

 searchLocation: {
 key: "search_location";
 type: "dict | None";
 persistence: "session";
 structure: {
 latitude: "float";
 longitude: "float";
 address: "str";
 };
 };

 solarResults: {
 key: "solar_results_advanced";
 type: "dict";
 persistence: "session";
 scope: "calculation_results";
 };
 };

 cacheManagement: {
 dataLoader: {
 function: "load_and_process_data";
 decorator: "@st.cache_data";
 ttl: 3600; // 1 hour
 clear_trigger: "refresh_button";
 };

 dpeCache: {
 function: "get_all_dpe_around_point";
 decorator: "@st.cache_data";
 ttl: 86400 * 30; // 30 days
 clear_trigger: "dpe_refresh_button";
 };

 communesCache: {
 function: "get_all_communes_dept_06";
 decorator: "@st.cache_data";
 ttl: 86400; // 24 hours
 static: true; // Rarely changes
 };
 };

 memoryOptimization: {
 dataTypes: {
 consommation_kwh: "float32"; // Instead of float64
 latitude: "float32";
 longitude: "float32";
 nombre_de_logements: "int16"; // Instead of int64
 };

 columnSelection: {
 required: ["consommation_kwh", "nom_commune", "latitude", "longitude", "adresse", "nombre_de_logements"];
 optional: ["location_confidence", "data_source", "nature_detaillee", "dpe_*"];
 dropUnused: true;
 };
 };
}
```

## Affichage des Résultats de Simulation

### Résultats Solaires Avancés
```typescript
interface SolarResultsDisplay {
 condition: "'solar_results_advanced' in st.session_state";
 title: " Analyse Terminée";

 summary: {
 layout: "info_banner";
 content: """
 **{layout['total_panels']} panneaux 440W** → **{layout['total_kwc']:.1f} kWc** |
 **{summary['production_annual_kwh']:,} kWh/an** |
 **{summary['self_consumption_rate']:.0f}% autoconsommé** |
 **ROI {financial['roi_years']:.1f} ans**
 """;
 };

 detailedResults: {
 layout: "tabs";

 tabs: [
 {
 id: "metrics";
 title: " Métriques";
 layout: "4_columns";

 metrics: [
 {
 label: "Production";
 value: "f\"{summary['production_annual_kwh']:,} kWh\"";
 delta: "f\"{summary['production_annual_kwh']/layout['total_kwc']:.0f} kWh/kWc\"";
 },
 {
 label: "Autoconso.";
 value: "f\"{summary['self_consumption_rate']:.1f}%\"";
 delta: "f\"{summary['autoconsumption_kwh']:,} kWh\"";
 },
 {
 label: "Autoprod.";
 value: "f\"{summary['self_production_rate']:.1f}%\"";
 delta: "f\"-{summary['grid_consumption_kwh']:,} kWh\"";
 },
 {
 label: "Puissance";
 value: "f\"{layout['total_kwc']:.1f} kWc\"";
 delta: "f\"{layout['total_panels']} panneaux\"";
 }
 ];
 },
 {
 id: "details";
 title: " Détails";

 alternatives: {
 condition: "'alternatives' in layout and layout['alternatives']";
 display: """
 for alt_name, alt_info in layout['alternatives'].items():
 st.caption(f"{alt_info['description']}: {alt_info['panels']} panneaux → {alt_info['kwc']} kWc")
 """;
 };

 calculationDetail: {
 condition: "'calculation_detail' in layout";
 display: """
 detail = layout['calculation_detail']
 preset = layout['efficiency_preset']
 st.caption(f'''
 **Méthode {layout['approach_used']}:** {preset['description']}
 - Surface: {detail['surface_brute']} m² → {detail['surface_utile']} m² utiles
 - Efficacité: {detail['efficacite_retenue']}
 - Panneaux: {detail['panneaux_theoriques']} théoriques → {detail['panneaux_installes']} installés
 ''')
 """;
 };
 },
 {
 id: "financial";
 title: " Financier";
 layout: "2_columns";

 leftColumn: [
 {
 metric: "Coût Installation";
 value: "f\"{financial['cout_installation']:,.0f} €\"";
 },
 {
 metric: "Économies/An";
 value: "f\"{financial['annual_savings']:,.0f} €\"";
 }
 ];

 rightColumn: [
 {
 metric: "ROI";
 value: "f\"{financial['roi_years']:.1f} ans\"";
 },
 {
 metric: "Économies 20 ans";
 value: "f\"{financial['savings_20_years']:,.0f} €\"";
 }
 ];

 sources: {
 expandable: true;
 title: " Sources";
 content: """
 - **Production:** {results.get('production_source', 'estimation')}
 - **Profils:** ADEME/RTE France
 - **API:** PVGIS (Commission Européenne)
 - **Calcul:** 8760 heures analysées
 """;
 };
 }
 ];
 };
}
```

## Performance et Métriques

### Indicateurs de Performance
```typescript
interface PerformanceMetrics {
 dataProcessing: {
 loadTime: {
 target: "<30s"; // Pour mode proximité Mougins
 measurement: "time_to_load_and_process_data";
 factors: [
 "network_latency",
 "api_response_time",
 "data_processing_time",
 "enrichment_time"
 ];
 };

 filteringSpeed: {
 target: "<500ms";
 measurement: "time_to_apply_filters";
 realTime: true;
 };

 statisticsCalculation: {
 target: "<100ms";
 measurement: "time_to_calculate_stats";
 components: [
 "basic_stats",
 "precision_quality",
 "legend_info"
 ];
 };
 };

 memoryUsage: {
 baseDataset: {
 target: "<50MB";
 measurement: "dataframe_memory_usage";
 optimization: "dtype_optimization";
 };

 sessionState: {
 target: "<10MB";
 measurement: "st_session_state_size";
 cleanup: "automatic";
 };
 };

 userExperience: {
 statisticsUpdate: {
 target: "<200ms";
 trigger: "filter_change";
 realTime: true;
 };

 exportGeneration: {
 target: "<5s";
 depends_on: "filtered_data_size";
 format: "CSV";
 };
 };
}
```

### Optimisations Implémentées
```typescript
interface PerformanceOptimizations {
 dataTypes: {
 purpose: "Réduction mémoire de 50%";
 optimizations: {
 consommation_kwh: "float32 au lieu de float64";
 coordinates: "float32 pour lat/lon";
 logements: "int16 au lieu de int64";
 categorical: "category dtype pour nom_commune";
 };
 };

 caching: {
 layers: [
 {
 level: "API_calls";
 functions: ["load_and_process_data", "get_all_dpe_around_point"];
 ttl: "1h - 30 jours";
 },
 {
 level: "session_state";
 data: ["filtered_data", "statistics"];
 persistence: "session";
 }
 ];
 };

 lazyEvaluation: {
 statistics: {
 trigger: "on_demand";
 expensive_operations: ["describe()", "value_counts()"];
 };

 export: {
 trigger: "button_click";
 generation: "just_in_time";
 };
 };

 chunking: {
 enabled: "large_datasets > 10k rows";
 chunk_size: 1000;
 processing: "streaming";
 };
}
```

## API et Intégrations

### Fonctions de Statistiques
```typescript
interface StatisticsFunctions {
 get_map_legend_info: {
 signature: "(filtered_data: pd.DataFrame) -> dict";
 purpose: "Calcule les informations de légende pour la carte";
 returns: {
 min_consumption: "float";
 mean_consumption: "float";
 max_consumption: "float";
 total_points: "int";
 };

 implementation: """
 return {
 'min_consumption': filtered_data['consommation_kwh'].min(),
 'mean_consumption': filtered_data['consommation_kwh'].mean(),
 'max_consumption': filtered_data['consommation_kwh'].max(),
 'total_points': len(filtered_data)
 }
 """;
 };

 calculate_precision_quality: {
 signature: "(data: pd.DataFrame) -> dict";
 purpose: "Évalue la qualité de précision des données géographiques";

 logic: """
 if len(data) == 0:
 return {'status': 'Analyse...', 'icon': '', 'quality_points': 0, 'total_points': 0}

 high_precision = data.filter(item => item.location_confidence === 'high').length
 osm_precision = data.filter(item => item.data_source === 'OSM').length
 quality_points = high_precision + osm_precision
 quality_rate = (quality_points / len(data)) * 100

 if quality_rate >= 30: status, icon = 'Bonne', ''
 elif quality_rate >= 10: status, icon = 'Moyenne', ''
 else: status, icon = 'Basique', ''

 return {'status': status, 'icon': icon, 'quality_points': quality_points, 'total_points': len(data)}
 """;
 };

 _show_statistics_summary: {
 signature: "(data: pd.DataFrame) -> None";
 purpose: "Affiche un résumé statistique détaillé des données filtrées";
 side_effects: "st.subheader, st.dataframe displays";

 components: [
 "consumption_statistics",
 "top_communes_analysis",
 "consumption_distribution"
 ];
 };
}
```

## Cas d'usage d'analyse

### Scénarios d'Analyse Typiques
```typescript
interface AnalysisScenarios {
 quickProspectAssessment: {
 description: "Évaluation rapide du potentiel d'une zone";
 workflow: [
 "Sélectionner mode proximité Mougins",
 "Observer les statistiques temps réel",
 "Analyser la répartition par tranches",
 "Identifier les communes prioritaires"
 ];

 keyMetrics: [
 "total_points > 1000",
 "average_consumption > 10000 kWh",
 "precision_quality = 'Bonne'"
 ];
 };

 targetedCampaign: {
 description: "Préparation d'une campagne ciblée";
 workflow: [
 "Filtrer par consommation > 15000 kWh",
 "Sélectionner communes spécifiques",
 "Exporter la liste en CSV",
 "Analyser les statistiques détaillées"
 ];

 deliverables: [
 "CSV avec coordonnées et consommations",
 "Résumé statistique par commune",
 "Répartition par tranches de consommation"
 ];
 };

 marketAnalysis: {
 description: "Analyse de marché départementale";
 workflow: [
 "Charger toutes les communes du 06",
 "Analyser les statistiques globales",
 "Comparer avec filtres sectoriels",
 "Générer résumés par zones"
 ];

 insights: [
 "Potentiel total du département",
 "Zones de forte densité de prospects",
 "Répartition géographique de la consommation"
 ];
 };
}
```

## Configuration technique

- **Calculs statistiques**: Pandas DataFrame operations (describe, value_counts, etc.)
- **Affichage metrics**: Streamlit st.metric avec deltas automatiques
- **Export de données**: CSV avec encoding UTF-8, nommage automatique
- **Session management**: Streamlit session_state avec optimisation mémoire
- **Performance**: Cache multi-niveaux, lazy evaluation, dtype optimization
- **Temps réel**: Recalcul automatique des statistiques lors de changements de filtres