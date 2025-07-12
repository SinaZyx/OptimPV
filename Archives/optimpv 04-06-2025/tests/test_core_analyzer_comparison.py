# tests/test_analysis_engine.py
import math
import numpy as np
import pandas as pd
import pytest
import sys
import os
import json
import copy # <--- AJOUTEZ CET IMPORT
from datetime import datetime, timedelta # <--- AJOUTEZ CET IMPORT

# --- Configuration des chemins (À ADAPTER PAR L'UTILISATEUR SI DIFFÉRENTS) ---
PATH_TO_OLD_ANALYZER = r"C:\\Users\\kingc\\OptimPV\\Archives\\modules 21-05-2025 14h27\\engine_module\\core_analyzer.py"
CONFIG_JSON_FILE_PATH = r"C:\\Users\\kingc\\OptimPV\\saved_configs\\config_Config_Projet_MultiSite_20250516_171843.json"

# Chemins vers les données des sites (EXEMPLE, adaptez si vous chargez les vrais fichiers)
# Si vous voulez utiliser les vrais fichiers Excel, décommentez et mettez les bons chemins.
# Sinon, le test utilisera `daily_profile_fixture_processed` pour simuler des données.
PATH_TO_SITE1_DATA = r"D:\\Downloads\\ABA V2 -45K3.xlsx"
# PATH_TO_SITE2_DATA = r"chemin/vers/ABA V2 -45K3 - Copie (2).xlsx" # Si vous avez plusieurs fichiers pour le test
# PATH_TO_SITE3_DATA = r"chemin/vers/ABA V2 -45K3 - Copie (3).xlsx"

# Nouvelle version (actuelle)
try:
    from modules.engine_module.core_analyzer import AnalysisEngine as AnalysisEngineNew
    from modules.engine_module.data_processing import validate_and_prepare_sites_data # Importé pour la fixture des données réelles
    print("INFO: Nouvelle version de AnalysisEngine chargée avec succès.")
except ImportError as e:
    AnalysisEngineNew = None
    print(f"ERREUR: Impossible de charger la nouvelle version de AnalysisEngine: {e}")
    # pytest.exit(f"Échec chargement nouvelle version AnalysisEngine: {e}")

# Ancienne version (depuis le dossier copié et renommé)
AnalysisEngineOld = None
try:
    # Assurez-vous que C:\Users\kingc\OptimPV est dans sys.path
    # Pytest le fait généralement s'il est lancé depuis C:\Users\kingc\OptimPV
    # Si vous avez un dossier C:\Users\kingc\OptimPV\engine_module_OLD_FOR_TEST\
    # contenant l'ancien code et un __init__.py :
    # Il est préférable de s'assurer que la racine du projet est dans sys.path si ce n'est pas garanti par l'environnement de test.
    project_root_path_for_old_engine = r"C:\Users\kingc\OptimPV"
    if project_root_path_for_old_engine not in sys.path:
        sys.path.insert(0, project_root_path_for_old_engine)

    from engine_module_OLD_FOR_TEST.core_analyzer import AnalysisEngine as AnalysisEngineOld
    print("INFO: Ancienne version de AnalysisEngine (depuis engine_module_OLD_FOR_TEST) chargée avec succès.")
except ModuleNotFoundError:
    print(f"AVERTISSEMENT: Module 'engine_module_OLD_FOR_TEST.core_analyzer' non trouvé.")
    print("  Assurez-vous d'avoir copié l'ancien 'engine_module' dans un dossier nommé 'engine_module_OLD_FOR_TEST'")
    print(f"  à la racine de votre projet (C:\\Users\\kingc\\OptimPV\\) et qu'il contient un __init__.py.")
except ImportError as e:
    print(f"AVERTISSEMENT: Ancienne version de AnalysisEngine (depuis engine_module_OLD_FOR_TEST) non importable: {e}")
except Exception as e_load_old:
    print(f"ERREUR inattendue lors du chargement de l'ancienne version: {e_load_old}")

# -----------------------------------------------------------------------------
#  Fixtures de Données
# -----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def config_data_from_json_fixture():
    """Charge la configuration complète (globale, sites, scénarios) depuis le fichier JSON."""
    if not os.path.exists(CONFIG_JSON_FILE_PATH):
        pytest.fail(f"Fichier de configuration JSON non trouvé : {CONFIG_JSON_FILE_PATH}")
    try:
        with open(CONFIG_JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            loaded_json = json.load(f)
        if "config" not in loaded_json or "sites_config" not in loaded_json or "scenarios" not in loaded_json:
            pytest.fail("Le fichier JSON de configuration n'a pas la structure attendue.")
        return loaded_json
    except Exception as e:
        pytest.fail(f"Erreur lors du chargement du fichier de configuration JSON : {e}")

@pytest.fixture(scope="function")
def base_config_from_json_fixture(config_data_from_json_fixture):
    """Fournit la section 'config' (globale) du JSON."""
    return copy.deepcopy(config_data_from_json_fixture.get("config", {}))

@pytest.fixture(scope="function")
def scenarios_from_json_fixture(config_data_from_json_fixture):
    """Fournit la section 'scenarios' du JSON."""
    return copy.deepcopy(config_data_from_json_fixture.get("scenarios", {}))

@pytest.fixture(scope="function")
def sites_config_from_json_fixture(config_data_from_json_fixture):
    """Fournit la section 'sites_config' du JSON."""
    return copy.deepcopy(config_data_from_json_fixture.get("sites_config", {}))

def load_and_prepare_site_excel_data(file_path, skiprows=18):
    """Charge et prépare minimalement un fichier Excel de site."""
    if not os.path.exists(file_path):
        print(f"AVERTISSEMENT: Fichier de données de site non trouvé à {file_path}")
        return None
    try:
        # Lire les noms de colonnes depuis la ligne où ils se trouvent réellement (souvent juste avant les données)
        # Si les noms sont à la ligne 19 (index 18), et les données commencent à la ligne 20 (index 19)
        # On lit la ligne 19 pour les en-têtes.
        # skiprows saute les lignes AVANT de lire. Donc si les données commencent à la ligne 20 (1-indexed),
        # on saute 19 lignes. Les en-têtes seraient à la ligne 19.
        # Cependant, PVSOL a souvent des en-têtes spécifiques.
        # Le fichier que vous avez fourni dans `DataImportModule` est lu avec skiprows=18
        # et les noms de colonnes sont ensuite pris de `df_headers` qui lit `nrows=1`.
        # Cela implique que les vrais noms de colonnes sont sur la TOUTE PREMIÈRE ligne du fichier,
        # puis il y a 17 lignes d'en-tête PVSOL, puis les données.
        # On va essayer de s'aligner sur la logique de DataImportModule.

        df_headers = pd.read_excel(file_path, nrows=1, engine='openpyxl')
        column_names_from_header_row = df_headers.columns.tolist()
        
        # Lire les données en sautant les lignes d'en-tête PVSOL et en utilisant les noms de la première ligne
        df_site = pd.read_excel(file_path, skiprows=skiprows, names=column_names_from_header_row, engine='openpyxl')
        print(f"INFO load_site_excel: Colonnes lues pour {os.path.basename(file_path)}: {df_site.columns.tolist()}")


        # Logique de détection des colonnes améliorée (plus flexible)
        time_col_name = None
        for potential_name in ['Temps', 'Date', 'Time', 'Période', column_names_from_header_row[0]]: # Ajout du premier nom de colonne comme fallback
            if potential_name in df_site.columns:
                time_col_name = potential_name
                break
        
        prod_col_name = None
        # Mots-clés pour la production, du plus spécifique au plus général
        prod_keywords = ['Énergie PV (CA) déduction faite de la consommation en veille', 'Énergie PV (CA)', 'Production PV', 'Énergie PV', 'production_kwh', 'Production']
        for keyword in prod_keywords:
            for col in df_site.columns:
                if keyword.lower() in col.lower(): # Recherche insensible à la casse et partielle
                    prod_col_name = col
                    break
            if prod_col_name:
                break
        if not prod_col_name and len(df_site.columns) > 1: # Fallback si non trouvé
            prod_col_name = df_site.columns[1]


        cons_col_name = None
        # Mots-clés pour la consommation
        cons_keywords = ['Consommation', 'consumption_kwh', 'Load', 'Charge']
        for keyword in cons_keywords:
            for col in df_site.columns:
                if keyword.lower() in col.lower():
                    cons_col_name = col
                    break
            if cons_col_name:
                break
        if not cons_col_name and len(df_site.columns) > 2: # Fallback
            cons_col_name = df_site.columns[2]
        elif not cons_col_name and len(df_site.columns) > 1 and prod_col_name != df_site.columns[1] : # autre fallback
             cons_col_name = df_site.columns[1]


        if not time_col_name: print(f"AVERTISSEMENT: Colonne 'Temps' non identifiée dans {file_path}. Utilisation de la première colonne par défaut.")
        if not prod_col_name: print(f"AVERTISSEMENT: Colonne 'Production' non identifiée dans {file_path}. Utilisation de la deuxième colonne par défaut.")
        if not cons_col_name: print(f"AVERTISSEMENT: Colonne 'Consommation' non identifiée dans {file_path}. Utilisation de la troisième colonne par défaut (ou la même que prod si seulement 2 colonnes).")

        time_col_name = time_col_name if time_col_name else df_site.columns[0]
        prod_col_name = prod_col_name if prod_col_name else (df_site.columns[1] if len(df_site.columns) > 1 else df_site.columns[0])
        cons_col_name = cons_col_name if cons_col_name else (df_site.columns[2] if len(df_site.columns) > 2 else prod_col_name) # Peut être le même que prod si peu de colonnes

        print(f"INFO load_site_excel: Colonnes mappées pour {os.path.basename(file_path)} -> Temps: '{time_col_name}', Prod: '{prod_col_name}', Cons: '{cons_col_name}'")

        df_processed = pd.DataFrame({
            'Temps': df_site[time_col_name],
            'production_kwh': pd.to_numeric(df_site[prod_col_name], errors='coerce').fillna(0),
            'consumption_kwh': pd.to_numeric(df_site[cons_col_name], errors='coerce').fillna(0)
        })

        # Conversion de la colonne 'Temps'
        # Le format 'DD.MM. HH:MM' est typique de PVSOL dans certaines configurations linguistiques.
        # Il faut lui ajouter l'année.
        # Supposons que les données sont pour la première année du projet (ou une année de référence).
        # La fixture `base_config_from_json_fixture` pourrait fournir l'année de début.
        # Pour ce test, on va prendre une année fixe ou l'année courante pour la conversion.
        
        start_year_for_data = datetime.now().year # Ou une année fixe si vous savez que vos données sont d'une année précise

        def convert_pvsol_time(time_val):
            if isinstance(time_val, (datetime, pd.Timestamp)):
                return time_val # Déjà au bon format
            try:
                # Format "DD.MM. HH:MM" (PVSOL typique)
                parts = str(time_val).split(' ')
                date_part = parts[0]
                time_part = parts[1]
                day, month = map(int, date_part.split('.')[0:2])
                hour, minute = map(int, time_part.split(':'))
                return datetime(start_year_for_data, month, day, hour, minute)
            except Exception:
                # Tentative avec pd.to_datetime pour d'autres formats
                dt = pd.to_datetime(time_val, errors='coerce')
                if pd.isna(dt):
                     print(f"AVERTISSEMENT: Échec conversion temps '{time_val}' pour {file_path}. Retourne NaT.")
                return dt

        df_processed['Temps'] = df_processed['Temps'].apply(convert_pvsol_time)
        df_processed = df_processed.dropna(subset=['Temps'])
        
        if df_processed.empty:
            print(f"AVERTISSEMENT: DataFrame vide après traitement pour {file_path}.")
        else:
            print(f"INFO load_site_excel: Premières lignes traitées pour {os.path.basename(file_path)}:\\n{df_processed.head()}")
            print(f"INFO load_site_excel: Somme prod={df_processed['production_kwh'].sum():.2f}, Somme cons={df_processed['consumption_kwh'].sum():.2f}")

        return df_processed

    except Exception as e:
        print(f"ERREUR lors du chargement du fichier de site {file_path}: {e}")
        # Retourner un DataFrame avec la structure attendue mais vide pour éviter des erreurs en aval
        return pd.DataFrame({'Temps': pd.Series(dtype='datetime64[ns]'), 'production_kwh': pd.Series(dtype='float64'), 'consumption_kwh': pd.Series(dtype='float64')})

@pytest.fixture(scope="session")
def actual_sites_data_fixture(config_data_from_json_fixture):
    """Charge les données réelles des sites mentionnés dans sites_config du JSON."""
    sites_config = config_data_from_json_fixture.get("sites_config", {})
    loaded_sites_data = {}
    
    # Déterminer le nombre de sites producteur/consommateur configurés
    # Ceci est juste pour l'information dans les logs du test.
    # Le moteur utilisera la config par site directement.
    num_prod_sites = sum(1 for scfg in sites_config.values() if scfg.get('site_type', 'Producteur') == 'Producteur')
    num_cons_pur_sites = sum(1 for scfg in sites_config.values() if scfg.get('site_type') == 'Consommateur Pur')
    print(f"INFO Fixture: Configuration JSON contient {len(sites_config)} sites ({num_prod_sites} Producteurs, {num_cons_pur_sites} Consommateurs Purs).")

    # Logique pour charger les fichiers Excel réels basés sur les clés de sites_config
    # Pour cet exemple, on va supposer que les clés correspondent aux noms de fichiers.
    # Et que le premier site est celui dont le chemin est fourni.
    
    # Exemple pour le premier site (ABA V2 -45K3.xlsx)
    site1_key_from_json = "ABA V2 -45K3.xlsx" # Clé telle qu'elle est dans votre JSON
    if site1_key_from_json in sites_config:
        df_site1 = load_and_prepare_site_excel_data(PATH_TO_SITE1_DATA)
        if df_site1 is not None and not df_site1.empty:
            loaded_sites_data[site1_key_from_json] = df_site1
            print(f"INFO Fixture: Données chargées pour le site '{site1_key_from_json}' depuis {PATH_TO_SITE1_DATA}")
        else:
            print(f"AVERTISSEMENT Fixture: Impossible de charger ou données vides pour {site1_key_from_json} depuis {PATH_TO_SITE1_DATA}")
    else:
        print(f"AVERTISSEMENT Fixture: La clé '{site1_key_from_json}' n'est pas dans sites_config du JSON.")

    # Vous devriez étendre cela pour charger les autres fichiers si vous en avez
    # et si leurs noms de fichiers correspondent aux clés dans sites_config.
    # Par exemple :
    # site2_key_from_json = "ABA V2 -45K3 - Copie (2).xlsx"
    # if site2_key_from_json in sites_config and os.path.exists(PATH_TO_SITE2_DATA):
    #     df_site2 = load_and_prepare_site_excel_data(PATH_TO_SITE2_DATA)
    #     if df_site2 is not None and not df_site2.empty:
    #         loaded_sites_data[site2_key_from_json] = df_site2
    #         # ... etc pour site 3

    if not loaded_sites_data:
        print("AVERTISSEMENT Fixture: Aucune donnée de site réelle n'a été chargée. Le test pourrait échouer ou utiliser des données vides.")
        # Pour permettre au test de tourner même sans les vrais fichiers, on pourrait retourner un site avec des données simulées.
        # Mais pour une comparaison fidèle, il faut les vraies données.
        # Retourner un dictionnaire vide si aucun site n'est chargé pour éviter les erreurs en aval.
        return {}
        
    return loaded_sites_data

# -----------------------------------------------------------------------------
#  Test principal de comparaison
# -----------------------------------------------------------------------------
PRIX_REVENTE_COMPARISON = 0.12 # Prix fixe pour comparer les VAN Projet

def test_compare_core_analyzer_versions(
    base_config_from_json_fixture,
    scenarios_from_json_fixture,
    sites_config_from_json_fixture,
    actual_sites_data_fixture
):
    if AnalysisEngineOld is None:
        pytest.skip("Ancienne version de AnalysisEngine (AnalysisEngineOld) non disponible pour la comparaison. Vérifiez PATH_TO_OLD_ANALYZER.")
    if AnalysisEngineNew is None:
        pytest.fail("Nouvelle version de AnalysisEngine (AnalysisEngineNew) n'a pas pu être chargée.")

    if not actual_sites_data_fixture or not isinstance(actual_sites_data_fixture, dict) or len(actual_sites_data_fixture) == 0:
        pytest.skip("Aucune donnée de site réelle n'a été chargée par actual_sites_data_fixture. Test de comparaison annulé.")
    
    sites_data_for_test = actual_sites_data_fixture

    print(f"\n--- Configuration Globale Utilisée (depuis JSON) ---")
    keys_to_log_config = ["capex_scenario", "puissance_kwc_installee", "debt_ratio", "taux_interet_dette", "cout_fonds_propres", "subvention_rate_le100", "opex_maintenance_fallback"]
    for key, value in base_config_from_json_fixture.items():
        if key in keys_to_log_config: print(f"  {key}: {value}")

    print(f"\n--- Configuration Spécifique des Sites Utilisée (depuis JSON) ---")
    if sites_config_from_json_fixture:
        for site_id, cfg_site in sites_config_from_json_fixture.items():
            print(f"  Site ID: {site_id} - Type: {cfg_site.get('site_type', 'N/A')}, P: {cfg_site.get('puissance_kwc', 'N/A')} kWc, CAPEX: {cfg_site.get('capex', 'N/A')}")
    else:
        print("  Aucune configuration spécifique par site (utilisation des paramètres globaux pour CAPEX/OPEX/Puissance).")

    print("\nInitialisation AnalysisEngineOld...")
    engine_old = AnalysisEngineOld(config=base_config_from_json_fixture, scenarios=scenarios_from_json_fixture, sites_data=sites_data_for_test)
    print("Initialisation AnalysisEngineNew...")
    engine_new = AnalysisEngineNew(config=base_config_from_json_fixture, scenarios=scenarios_from_json_fixture, sites_data=sites_data_for_test)

    # --- Test avec un prix de revente fixe ---
    print(f"\n--- Exécution ANCIENNE version (core_analyzer_OLD.py) ---")
    print(f"Prix de revente fixe pour comparaison: {PRIX_REVENTE_COMPARISON} €/kWh")
    results_old = engine_old.calculate_financial_indicators(
        scenario_name="Base", prix_revente=PRIX_REVENTE_COMPARISON, sites_config=sites_config_from_json_fixture
    )
    assert results_old is not None, "results_old ne doit pas être None"
    if "error" in results_old: pytest.fail(f"Erreur calcul ANCIENNE version: {results_old['error']}")
    df_old = results_old['monthly_data']
    npv_project_old = results_old.get('npv_project', np.nan)
    print(f"ANCIEN - NPV Projet: {npv_project_old:.2f}")

    print(f"\n--- Exécution NOUVELLE version (core_analyzer.py) ---")
    print(f"Prix de revente fixe pour comparaison: {PRIX_REVENTE_COMPARISON} €/kWh")
    results_new = engine_new.calculate_financial_indicators(
        scenario_name="Base", prix_revente=PRIX_REVENTE_COMPARISON, sites_config=sites_config_from_json_fixture
    )
    assert results_new is not None, "results_new ne doit pas être None"
    if "error" in results_new: pytest.fail(f"Erreur calcul NOUVELLE version: {results_new['error']}")
    df_new = results_new['monthly_data']
    npv_project_new = results_new.get('npv_project', np.nan)
    print(f"NOUVEAU - NPV Projet: {npv_project_new:.2f}")

    print(f"\n--- Comparaison NPV Projet (Prix Fixe = {PRIX_REVENTE_COMPARISON} €/kWh) ---")
    print(f"  NPV Projet (Ancien): {npv_project_old:.2f}")
    print(f"  NPV Projet (Nouveau): {npv_project_new:.2f}")
    if pd.notna(npv_project_old) and pd.notna(npv_project_new):
        diff_npv = npv_project_new - npv_project_old
        print(f"  Différence NPV (Nouveau - Ancien): {diff_npv:.2f}")
        if abs(diff_npv) > 1.0: print(f"  CONCLUSION NPV: La nouvelle version donne une VAN Projet {'plus élevée' if diff_npv > 0 else 'plus basse'}.")
        else: print(f"  CONCLUSION NPV: Les VAN Projet sont très similaires.")
    else: print("  CONCLUSION NPV: Impossible de calculer la différence car une ou plusieurs VAN sont NaN.")

    cols_to_compare = [
        'OCF_Projet', 'EBITDA', 'EBIT', 'Amortissement', 'CAPEX_Initial_Mensuel',
        'Prime_Autoconso_Encaissee', 'Delta_BFR_Mensuel', 'VAT_Payment',
        'Total_IS_Decaisse_Mois', 'Interets_Payes', 'Principal_Rembourse',
        'Revenus_Total',
        # 'Nopat_Mensuel', # Potentiellement absente si non stockée explicitement
        # 'Impot_Theorique_Sur_EBIT_Mensuel' # Idem
    ]

    print("\n--- Comparaison des SOMMES des Colonnes Clés Mensuelles (sur toute la durée) ---")
    all_cols_similar_sums = True
    for col in cols_to_compare:
        sum_old, sum_new = np.nan, np.nan
        print(f"Colonne: {col}")
        if col in df_old.columns: sum_old = df_old[col].sum(); print(f"  Somme Ancienne Version: {sum_old:.2f}")
        else: print(f"  Colonne '{col}' absente dans l'ancienne version.")
        if col in df_new.columns: sum_new = df_new[col].sum(); print(f"  Somme Nouvelle Version: {sum_new:.2f}")
        else: print(f"  Colonne '{col}' absente dans la nouvelle version.")
        if pd.notna(sum_old) and pd.notna(sum_new):
            diff_sum = sum_new - sum_old
            if abs(diff_sum) > 1e-2: print(f"  >> Différence (Nouveau - Ancien): {diff_sum:.2f} <<"); all_cols_similar_sums = False
        elif pd.isna(sum_old) != pd.isna(sum_new): print(f"  >> Différence de présence/calcul pour la colonne '{col}'."); all_cols_similar_sums = False
        print("-" * 20)
    if all_cols_similar_sums: print(">> Toutes les sommes des colonnes comparées sont similaires (ou une colonne manquait symétriquement).")

    print("\n--- Calcul et Comparaison Prix Plancher (VAN Projet = 0) ---")
    print("Calcul pour ANCIENNE version...")
    results_van0_old = engine_old.simulate_selling_price("Base", target_npv=0, sites_config=sites_config_from_json_fixture)
    prix_plancher_old = np.nan
    if results_van0_old and "error" not in results_van0_old:
        prix_plancher_old = results_van0_old.get("prix_revente_optimal_pour_cible", np.nan)
        print(f"ANCIEN - Prix Plancher VAN Projet=0: {prix_plancher_old:.4f} €/kWh")
    else: print(f"ANCIEN - Échec calcul prix plancher: {results_van0_old.get('error', 'Erreur inconnue') if results_van0_old else 'Pas de résultats'}")

    print("Calcul pour NOUVELLE version...")
    results_van0_new = engine_new.simulate_selling_price("Base", target_npv=0, sites_config=sites_config_from_json_fixture)
    prix_plancher_new = np.nan
    if results_van0_new and "error" not in results_van0_new:
        prix_plancher_new = results_van0_new.get("prix_revente_optimal_pour_cible", np.nan)
        print(f"NOUVEAU - Prix Plancher VAN Projet=0: {prix_plancher_new:.4f} €/kWh")
    else: print(f"NOUVEAU - Échec calcul prix plancher: {results_van0_new.get('error', 'Erreur inconnue') if results_van0_new else 'Pas de résultats'}")

    if pd.notna(prix_plancher_old) and pd.notna(prix_plancher_new):
        diff_prix_plancher = prix_plancher_new - prix_plancher_old
        print(f"DIFFERENCE Prix Plancher (Nouveau - Ancien): {diff_prix_plancher:.4f} €/kWh")
        if abs(diff_prix_plancher) < 1e-4: print(">> Les prix planchers sont quasi identiques.")
        elif diff_prix_plancher < 0: print(">> Le prix plancher de la NOUVELLE version est PLUS BAS.")
        else: print(">> Le prix plancher de la NOUVELLE version est PLUS HAUT.")
    else: print(">> Impossible de comparer les prix planchers car l'un ou les deux n'ont pas pu être calculés.")