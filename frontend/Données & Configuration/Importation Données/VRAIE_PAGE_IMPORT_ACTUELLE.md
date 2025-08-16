# Page d'Importation de Données - Module Actuel OptimPV

## Vue d'ensemble

La page d'importation de données d'OptimPV permet l'import de fichiers de production et consommation photovoltaïque, principalement depuis PV*SOL, avec gestion multi-sites et mapping automatique des colonnes.

## Structure de la page actuelle

### Header Principal
```python
interface ImportHeader {
 title: "Importation des Données";
 className: "main-header";

 description: "Interface pour l'upload de fichiers PVSOL (Multi-sites)";

 status: {
 sites_imported: number;
 data_imported: boolean;
 session_state: "sites_data";
 };
}
```

### Section Upload Multi-Fichiers
```python
interface MultiFileUpload {
 component: "st.file_uploader";

 configuration: {
 label: "Importer un ou plusieurs fichiers Excel de PVSOL (un par site)";
 type: ["xlsx", "xls"];
 accept_multiple_files: true;
 key: "pvsol_excel_uploader";
 };

 processing: {
 per_file: {
 site_id: "uploaded_file.name"; # Nom fichier = ID site

 read_strategy: {
 engine: "openpyxl";
 skiprows: 18; # Format PV*SOL standard
 headers_row: 1; # Récupération noms colonnes
 };

 preview: {
 expandable: true;
 label: f"Voir Aperçu Données Brutes pour {site_id}";
 content: "df_pvsol.head()";
 };
 };
 };
}
```

### Mapping Intelligent des Colonnes
```python
interface ColumnMapping {
 auto_detection: {
 date_columns_priority: [
 "Temps", "Date", "DateTime", "Time"
 ];

 production_columns_priority: [
 "Énergie PV (CC)",
 "Production PV",
 "Énergie PV",
 "Production",
 "PV Energy"
 ];

 consumption_columns_priority: [
 "Consommation",
 "Consumption",
 "Load"
 ];

 algorithm: {
 exact_match: boolean; # Recherche correspondance exacte
 partial_match: boolean; # Recherche dans sous-chaînes
 fallback: "default_index"; # Si aucune correspondance
 };
 };

 user_interface: {
 layout: "3_columns";

 selectors: [
 {
 id: "date_col";
 label: "Colonne Date/Heure";
 options: "available_columns";
 index: "auto_detected_date_index";
 key: f"map_{site_id}_date_col";
 },
 {
 id: "prod_col";
 label: "Colonne Production PV";
 options: "available_columns";
 index: "auto_detected_prod_index";
 key: f"map_{site_id}_prod_col";
 },
 {
 id: "cons_col";
 label: "Colonne Consommation";
 options: "available_columns";
 index: "auto_detected_cons_index";
 key: f"map_{site_id}_cons_col";
 }
 ];

 duplication_prevention: {
 avoid_same_column: true;
 smart_fallback: true;
 };
 };
}
```

### Traitement et Standardisation
```python
interface DataProcessing {
 standardization_block: {
 date_conversion: {
 primary_method: "convert_date_format()"; # Format 'dd.mm hh:mm'
 fallback_method: "pd.to_datetime()";

 validation: {
 check_null_values: true;
 error_on_conversion_failure: true;
 };
 };

 numeric_processing: {
 production_kwh: {
 conversion: "pd.to_numeric()";
 fill_na: 0.0;
 clip_negative: true; # Assure valeurs >= 0
 fallback_if_missing: 0.0; # Site consommateur pur
 };

 consumption_kwh: {
 conversion: "pd.to_numeric()";
 fill_na: 0.0;
 clip_negative: true;
 fallback_if_missing: 0.0; # Site producteur pur
 };
 };

 final_formatting: {
 columns_order: ["Temps", "production_kwh", "consumption_kwh"];
 sort_by: "Temps";
 drop_na_time: true;
 };
 };

 storage: {
 session_state_key: "sites_data";
 data_structure: "Dict[site_id, DataFrame]";

 success_actions: {
 set_data_imported: true;
 force_rerun: "st.rerun()";
 success_message: f"Données pour le site '{site_id}' traitées et standardisées.";
 };
 };
}
```

### Gestion des Sites Importés
```python
interface SitesManagement {
 display_section: {
 title: "Sites Actuellement Importés";
 visibility: "if st.session_state.sites_data";

 layout: "dynamic_columns"; # Une colonne par site

 site_card: {
 title: "site_id";
 subtitle: f"{len(site_df)} lignes";

 actions: {
 delete: {
 button: f"Supprimer {site_id}";
 key: f"delete_{site_id}";
 help: "Supprimer les données de ce site";

 logic: {
 remove_from_dict: true;
 update_data_imported_flag: true;
 rerun_if_empty: true;
 };
 };
 };
 };
 };

 bulk_actions: {
 reset_all: {
 condition: "len(sites_data) > 1";
 button: "Réinitialiser Tous les Sites Importés";

 action: {
 clear_sites_data: true;
 set_data_imported_false: true;
 force_rerun: true;
 };
 };
 };

 empty_state: {
 message: "Aucun site importé pour le moment. Utilisez le bouton ci-dessus pour charger les fichiers.";
 type: "st.info";
 };
}
```

## Fonctionnalités Techniques

### Algorithmes de Détection
```python
class ColumnDetection {
 def find_column_index(columns: List[str], priority_list: List[str]) -> int:
 # 1. Recherche correspondances exactes
 for priority in priority_list:
 if priority in columns:
 return columns.index(priority)

 # 2. Recherche correspondances partielles
 for priority in priority_list:
 for i, col in enumerate(columns):
 if priority.lower() in col.lower():
 return i

 # 3. Fallback à index 0
 return 0 if columns else None
}
```

### Conversion de Dates PV*SOL
```python
def convert_date_format(date_str: str, year: int = None) -> datetime:
 """
 Convertit format PV*SOL 'DD.MM. HH:mm' en datetime

 Exemples formats supportés:
 - "01.01. 12:30"
 - "15.06. 09:15"
 - "31.12. 23:45"
 """
 try:
 day, month = date_str.split('.')[0:2]
 hour, minute = date_str.split(' ')[1].split(':')

 return datetime(
 year=year or datetime.now().year,
 month=int(month.strip()) or 1,
 day=int(day),
 hour=int(hour),
 minute=int(minute)
 )
 except Exception as e:
 st.error(f"Erreur conversion date '{date_str}': {e}")
 return None
```

### Debug et Validation
```python
interface DebugSystem {
 verbose_logging: {
 file_reading: {
 "CSV avec sep=';'": "df.head() + colonnes + nb_lignes";
 "Excel skiprows=18": "df.head() + colonnes + nb_lignes";
 };

 processing: {
 "Colonnes détectées": "production_cols + date_cols";
 "Sélection finale": "date_col + production_col";
 "Échantillons données": "df[col].head().tolist()";
 };

 validation: {
 "Production totale": "numeric_values.sum()";
 "Alertes si quasi-nulle": "< 1.0 kWh";
 "Min/Max production": "df['production_kwh'].min/max()";
 };
 };

 error_handling: {
 file_reading_errors: "Multiple separator attempts";
 date_conversion_errors: "Primary + fallback methods";
 numeric_conversion_errors: "Graceful degradation";
 missing_columns_warnings: "Site-specific warnings";
 };
}
```

## Structures de Données

### Session State
```python
session_state_structure = {
 "sites_data": {
 type: "Dict[str, pd.DataFrame]";
 key_format: "filename.xlsx";
 value_format: {
 columns: ["Temps", "production_kwh", "consumption_kwh"];
 dtypes: {
 "Temps": "datetime64[ns]";
 "production_kwh": "float64";
 "consumption_kwh": "float64";
 };
 };
 };

 "data_imported": {
 type: "bool";
 purpose: "Flag global d'import réussi";
 updated_when: ["successful_processing", "site_deletion", "reset_all"];
 };

 "production_data": "Optional[pd.DataFrame]"; # Legacy
 "consumption_data": "Optional[pd.DataFrame]"; # Legacy
 "processed_data": "Optional[pd.DataFrame]"; # Legacy
}
```

### Format Fichier Attendu (PV*SOL)
```python
pvsol_file_format = {
 extension: [".xlsx", ".xls"];
 structure: {
 headers_row: 1; # Noms de colonnes
 data_start_row: 19; # skiprows=18

 expected_columns: {
 date: ["Temps", "Date", "DateTime"];
 production: ["Énergie PV (CC)", "Production PV", "Énergie PV"];
 consumption: ["Consommation", "Consumption", "Load"];
 };

 date_format: "dd.mm. hh:mm"; # Ex: "01.01. 12:30"
 numeric_format: {
 decimal_separator: "," | ".";
 handling: "automatic_conversion";
 };
 };
}
```

## Flux Utilisateur

### Workflow Complet
```python
user_workflow = {
 step_1: {
 action: "Upload fichiers Excel PV*SOL";
 multiple: true;
 validation: "Extension.xlsx/.xls";
 };

 step_2: {
 per_file: {
 action: "Lecture et aperçu automatique";
 preview: "Expandable data preview";
 auto_detection: "Colonnes date/production/consommation";
 };
 };

 step_3: {
 action: "Ajustement mapping colonnes";
 interface: "3 selectbox par fichier";
 validation: "Anti-duplication colonnes";
 };

 step_4: {
 action: "Traitement et standardisation";
 trigger: f"Bouton 'Traiter pour {site_id}'";
 feedback: "Spinner + messages succès/erreur";
 };

 step_5: {
 action: "Gestion sites importés";
 options: ["Visualisation", "Suppression individuelle", "Reset global"];
 persistence: "Session state";
 };
}
```

## Intégration avec OptimPV

### Utilisation dans app.py
```python
# app.py ligne 539
if selected_page == "Importation Données":
 if 'data_import_module' not in st.session_state:
 from modules.data_import import DataImportModule
 st.session_state.data_import_module = DataImportModule()

 st.session_state.data_import_module.show_ui()
```

### Exploitation des Données
```python
data_usage = {
 access_pattern: "st.session_state.sites_data[site_id]";

 typical_operations: [
 "Production/consommation totales par site",
 "Calculs d'autoconsommation",
 "Agrégation multi-sites",
 "Analyses temporelles",
 "Export vers autres modules"
 ];

 data_format: {
 guaranteed_columns: ["Temps", "production_kwh", "consumption_kwh"];
 guaranteed_types: ["datetime64", "float64", "float64"];
 guaranteed_order: "Triée par Temps croissant";
 };
}
```

## Limitations et Améliorations

### Limitations Actuelles
```python
current_limitations = {
 file_formats: {
 supported: ["Excel PV*SOL uniquement"];
 missing: ["CSV générique", "JSON", "autres logiciels PV"];
 };

 validation: {
 minimal_data_validation: true;
 no_time_continuity_check: true;
 no_outlier_detection: true;
 };

 storage: {
 session_only: true;
 no_persistent_storage: true;
 no_project_association: true;
 };

 interface: {
 no_batch_operations: true;
 limited_preview: true;
 no_data_transformation: true;
 };
}
```

### Améliorations Possibles
```python
improvements = {
 formats: {
 "Support CSV générique": "Détection automatique séparateurs";
 "Support JSON/API": "Import depuis services web";
 "Support autres logiciels": "Helioscope, PVSyst, etc.";
 };

 validation: {
 "Contrôles qualité": "Outliers, gaps, cohérence";
 "Métriques automatiques": "Facteur charge, ratios";
 "Alertes intelligentes": "Anomalies détectées";
 };

 interface: {
 "Aperçu avancé": "Graphiques, statistiques";
 "Transformation données": "Agrégation, resampling";
 "Templates mapping": "Sauvegarde configurations";
 };

 integration: {
 "Liaison projets": "Association import-projet";
 "Stockage permanent": "Base de données";
 "API REST": "Import programmatique";
 };
}
```

Cette page d'import constitue le point d'entrée principal pour les données énergétiques dans OptimPV, avec un focus sur la simplicité d'usage et la robustesse du traitement des formats PV*SOL.