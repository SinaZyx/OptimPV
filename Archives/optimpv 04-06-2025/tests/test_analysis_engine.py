# tests/test_analysis_engine.py
import math
import numpy as np
import pandas as pd
import pytest
import sys
import os
import json
import copy
from datetime import datetime, timedelta

# --- Configuration des chemins (À ADAPTER SI NÉCESSAIRE) ---
CONFIG_JSON_FILE_PATH = r"C:\\Users\\kingc\\OptimPV\\saved_configs\\config_Config_Projet_MultiSite_20250516_171843.json"
PATH_TO_SITE1_DATA_FOR_TEST = r"D:\\Downloads\\ABA V2 -45K3.xlsx"

# --- Imports des modules de l'application ---
try:
    from modules.engine_module.core_analyzer import AnalysisEngine
    from modules.engine_module.financial_calculations import calculate_wacc, calculate_lcoe_annual_aggregation
    # Importer calculate_lcoe_engineering si vous voulez aussi le tester unitairement
    # from modules.engine_module.financial_calculations import calculate_lcoe_engineering
except ImportError as e:
    print(f"ERREUR D'IMPORT dans test_analysis_engine.py: {e}")
    sys.exit(1)

# -----------------------------------------------------------------------------
#  Fixtures (celles définies précédemment pour charger config et données de site)
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session")
def config_data_from_json_fixture_for_engine_tests():
    if not os.path.exists(CONFIG_JSON_FILE_PATH): #
        pytest.fail(f"Fichier de configuration JSON non trouvé : {CONFIG_JSON_FILE_PATH}")
    try:
        with open(CONFIG_JSON_FILE_PATH, 'r', encoding='utf-8') as f: #
            loaded_json = json.load(f) #
        if "config" not in loaded_json or "sites_config" not in loaded_json or "scenarios" not in loaded_json: #
            pytest.fail("Le fichier JSON de configuration n'a pas la structure attendue.")
        return loaded_json
    except Exception as e:
        pytest.fail(f"Erreur lors du chargement du fichier de configuration JSON : {e}")

@pytest.fixture(scope="function")
def base_config_real(config_data_from_json_fixture_for_engine_tests): #
    return copy.deepcopy(config_data_from_json_fixture_for_engine_tests.get("config", {})) #

@pytest.fixture(scope="function")
def scenarios_real(config_data_from_json_fixture_for_engine_tests): #
    return copy.deepcopy(config_data_from_json_fixture_for_engine_tests.get("scenarios", {})) #

@pytest.fixture(scope="function")
def sites_config_real(config_data_from_json_fixture_for_engine_tests): #
    return copy.deepcopy(config_data_from_json_fixture_for_engine_tests.get("sites_config", {})) #

def load_and_prepare_single_site_excel_data_for_test(file_path, skiprows=18): #
    if not os.path.exists(file_path): #
        print(f"AVERTISSEMENT: Fichier de données de site non trouvé à {file_path}")
        return None
    try:
        df_headers = pd.read_excel(file_path, nrows=1, engine='openpyxl') #
        column_names_from_header_row = df_headers.columns.tolist() #
        df_site = pd.read_excel(file_path, skiprows=skiprows, names=column_names_from_header_row, engine='openpyxl') #

        time_col_found = next((col for col in df_site.columns if 'Temps' in col), df_site.columns[0]) #
        prod_col_found = next((col for col in df_site.columns if 'Énergie PV nominale' in col or 'production' in col.lower()), df_site.columns[1]) #
        cons_col_found = next((col for col in df_site.columns if 'Consommation' in col or 'consumption' in col.lower()), df_site.columns[2]) #

        df_processed = pd.DataFrame({
            'Temps': df_site[time_col_found], #
            'production_kwh': pd.to_numeric(df_site[prod_col_found], errors='coerce').fillna(0), #
            'consumption_kwh': pd.to_numeric(df_site[cons_col_found], errors='coerce').fillna(0) #
        })
        print(f"INFO: Données brutes chargées pour {os.path.basename(file_path)} avant passage à AnalysisEngine.") #
        return df_processed
    except Exception as e:
        print(f"ERREUR lors du chargement du fichier de site {file_path} pour test_analysis_engine: {e}")
        return None

@pytest.fixture(scope="function")
def single_site_real_data_fixture(): #
    df_site = load_and_prepare_single_site_excel_data_for_test(PATH_TO_SITE1_DATA_FOR_TEST) #
    if df_site is None or df_site.empty: #
        pytest.skip(f"Impossible de charger les données du site depuis {PATH_TO_SITE1_DATA_FOR_TEST}. Test annulé.")
    site_key = os.path.basename(PATH_TO_SITE1_DATA_FOR_TEST) #
    return {site_key: df_site} #

# --- Fixtures pour données contrôlées (déjà fournies et corrigées) ---
@pytest.fixture(scope="function")
def simple_monthly_data_lcoe(): #
    """Crée un DataFrame mensuel simple pour tester le LCOE."""
    # Projet sur 2 ans (24 mois), CAPEX en M0, exploitation à partir de M1
    # Construction = 0 mois pour ce flux simple LCOE (CAPEX au début de l'exploitation)
    dates = pd.date_range(start="2025-01-01", periods=24, freq='ME') #
    df = pd.DataFrame(index=dates) #
    df['Is_Construction_Phase'] = 0.0 #
    df['CAPEX_Initial_Mensuel'] = 0.0 #
    # CAPEX de 10000 en début de première période (pour T0 du LCOE avec construction_mois=0)
    # Si construction_mois=0, AnalysisEngine s'attend à ce que le CAPEX du premier mois d'exploitation
    # soit le montant_capex_pour_financement_et_flux.
    # Pour le test direct de calculate_lcoe_annual_aggregation, on met le CAPEX via la fixture
    # au premier mois, et on s'assure que construction_period_months=0 est passé.
    df.iloc[0, df.columns.get_loc('CAPEX_Initial_Mensuel')] = 10000
    
    df['OPEX'] = 100 #
    df['TURPE'] = 50  #
    df['Production_kWh'] = 1000 #
    return df #

@pytest.fixture(scope="function")
def monthly_data_construction_interest(): #
    """Crée un DataFrame mensuel pour tester les intérêts capitalisés."""
    # 3 mois de construction, puis 21 mois d'exploitation
    total_months = 24 #
    construction_months = 3 #
    dates = pd.date_range(start="2025-01-01", periods=total_months, freq='ME') #
    df = pd.DataFrame(index=dates) #
    
    df['Is_Construction_Phase'] = 0.0 #
    df.iloc[:construction_months, df.columns.get_loc('Is_Construction_Phase')] = 1.0 #
    
    df['CAPEX_Initial_Mensuel'] = 0.0 #
    # Le moteur de calcul des indicateurs va calculer Debt_Drawn_This_Month basé sur
    # le CAPEX total (ici 12000) et le répartir. La fixture n'a pas besoin de simuler les Debt_Drawn.
    # La fixture doit fournir les CAPEX_Initial_Mensuel que le moteur utilisera.
    # Le moteur s'attend à ce que la somme des CAPEX_Initial_Mensuel soit égale au CAPEX total du projet.
    # Pour ce test, le CAPEX_Initial_Mensuel n'est pas directement utilisé pour les tirages de dette
    # par la logique de test actuelle, mais par la logique interne de l'engine.
    # On le garde pour la cohérence si on voulait tester cet aspect plus tard.
    # Pour le test actuel des intérêts capitalisés, l'important est le `capex_scenario` dans la config.
    
    cols_to_fill = ['OPEX', 'TURPE', 'Production_kWh', 'Consommation_kWh',  #
                    'Revenus_Total', 'Amortissement', 'EBITDA', 'EBIT', 'EBT',  #
                    'Tax_Payment', 'Total_IS_Decaisse_Mois', 'Resultat_Net', #
                    'VAT_Payment', 'Delta_BFR_Mensuel', 'Prime_Autoconso_Encaissee', #
                    'Debt_Drawn_This_Month', 'Principal_Rembourse', 'Interets_Payes', #
                    'Solde_Dette_Fin_Mois', 'Service_Dette', 'FCFE', 'OCF_Projet', #
                    'Solde_Tresorerie_Fin_Mois'] #
    for col in cols_to_fill: #
        df[col] = 0.0 #
    return df #

# --- NOUVELLE FIXTURE pour test de temporalité ---
@pytest.fixture(scope="function")
def data_for_temporal_test_fixture(base_config_real):
    """Crée des données horaires pour un projet avec construction et exploitation décalées."""
    # Durée construction: 15 mois, Exploitation: 18 ans + 3 mois = 219 mois
    # Date début exploitation (PPA) sera fixée dans le test à "2027-01-01"
    # Donc, la construction commencerait 15 mois avant: Oct 2025.
    # Les données horaires doivent couvrir de Oct 2025 à Mar 2045.
    
    config_start_ppa_date = pd.to_datetime(base_config_real.get("date_debut_ppa","2027-01-01"))
    construction_duration_months_fixture = 15
    exploitation_duration_months_fixture = (18 * 12) + 3
    
    # Date de début de la simulation (et donc des données horaires nécessaires)
    data_start_date = config_start_ppa_date - pd.DateOffset(months=construction_duration_months_fixture)
    
    total_simulation_months_fixture = construction_duration_months_fixture + exploitation_duration_months_fixture
    # Calculer la date de fin des données horaires
    # date_range est inclusif pour start et end si on ne spécifie pas periods.
    # Pour être sûr de couvrir, on peut prendre un peu plus large ou calculer précisément.
    # Si ME, le dernier jour du mois est pris.
    end_date_for_data_generation = data_start_date + pd.DateOffset(months=total_simulation_months_fixture)
    
    hourly_index = pd.date_range(start=data_start_date, end=end_date_for_data_generation, freq='h', inclusive='left')
    
    df = pd.DataFrame(index=hourly_index)
    # Convertir l'index Datetime en string au format attendu par validate_and_prepare_sites_data
    # si celui-ci s'attend à un format string initial.
    # Cependant, AnalysisEngine appellera validate_and_prepare_sites_data qui peut gérer un DatetimeIndex.
    # Pour la cohérence avec la fixture de chargement Excel, on peut formater en string.
    # df['Temps'] = df.index.strftime('%Y-%m-%d %H:%M:%S') # Format standard que pd.to_datetime gère bien
    df['Temps'] = df.index # Laisser en DatetimeIndex, validate_and_prepare_sites_data le gère

    # Profils simples pour cet exemple
    df['production_kwh'] = np.where((df.index.hour >= 8) & (df.index.hour < 17), 5.0 * (np.sin(df.index.dayofyear / 365.25 * 2 * np.pi - np.pi/2) + 1.5), 0.0)
    df['consumption_kwh'] = 3.0 + 2.0 * np.sin(df.index.hour / 24.0 * 2 * np.pi)
    df.loc[df['production_kwh'] < 0, 'production_kwh'] = 0 # Assurer non-négatif
    df.loc[df['consumption_kwh'] < 0, 'consumption_kwh'] = 0

    # Retourner un dictionnaire comme attendu par AnalysisEngine
    return {"site_temporal_fixture": df[['Temps', 'production_kwh', 'consumption_kwh']].reset_index(drop=True)}

# -----------------------------------------------------------------------------
# Tests Unitaires et d'Intégration Existants et Nouveaux
# -----------------------------------------------------------------------------

# --- Tests WACC (inchangés) ---
wacc_cases = [
    (0.0, 4.0, 25.0, 8.0, 8.0), #
    (1.0, 4.0, 25.0, 8.0, 3.0), #
    (0.8, 4.0, 25.0, 8.0, 4.0), #
    (0.5, 0.0, 0.0, 8.0, 4.0), #
    (0.6, 5.0, 25.0, 10.0, 6.25), #
]
@pytest.mark.parametrize("dr, rd, tc, re, expected", wacc_cases) #
def test_calculate_wacc_numeric(dr, rd, tc, re, expected): #
    wacc = calculate_wacc(dr, rd, tc, re, wacc_type="after_tax") #
    assert wacc is not None, "Le WACC ne doit pas être None" #
    assert math.isclose(wacc, expected, rel_tol=1e-9), f"WACC {wacc}% ≠ attendu {expected}%" #

# -----------------------------------------------------------------------------
# Tests d'intégration : MODIFIÉ pour vérifier le TRI Projet avec différents niveaux de dette
# -----------------------------------------------------------------------------
# Cas de test : (debt_ratio, cout_fp_pct, taux_interet_dette_pct, with_subvention, attendu_wacc_pct, attendu_tri_projet_min_pct, attendu_tri_projet_max_pct)
# On ajoute des bornes pour le TRI Projet attendu. Ces bornes sont des estimations et devront être ajustées.
# --- Tests TRI Projet et WACC (avec fourchettes ajustées) ---
param_cases_tri_projet = [
    (0.0, 8.0, 4.0, True, 8.00, 5.5, 7.0), #
    (0.8, 8.0, 4.0, True, 4.00, 5.5, 7.0), #
    (0.9, 8.0, 4.0, True, 3.50, 5.5, 7.0), # WACC corrigé #
    (0.0, 8.0, 4.0, False, 8.00, 4.0, 5.5), #
    (0.8, 8.0, 4.0, False, 4.00, 4.0, 5.5), #
    (0.8, 8.0, 7.0, True, 5.80, 5.5, 7.0), # WACC corrigé #
]
@pytest.mark.parametrize(
    "debt_ratio, cout_fp_pct, taux_interet_dette_pct, with_subvention, expected_wacc_pct, tri_projet_min_expected, tri_projet_max_expected",
    param_cases_tri_projet
) #
def test_project_irr_with_debt_levels(
    base_config_real, scenarios_real, sites_config_real, single_site_real_data_fixture,
    debt_ratio, cout_fp_pct, taux_interet_dette_pct, with_subvention, expected_wacc_pct,
    tri_projet_min_expected, tri_projet_max_expected
): #
    cfg = base_config_real.copy() #
    cfg.update({
        "debt_ratio": debt_ratio, #
        "with_loan": debt_ratio > 0, #
        "cout_fonds_propres": cout_fp_pct, #
        "taux_interet_dette": taux_interet_dette_pct, #
    })
    if not with_subvention: #
        cfg["subvention_rate_le3"] = 0.0 #
        cfg["subvention_rate_le9"] = 0.0 #
        cfg["subvention_rate_le36"] = 0.0 #
        cfg["subvention_rate_le100"] = 0.0 #
        cfg["subvention_rate_le500"] = 0.0 #
        print("  TESTING WITHOUT SUBVENTION") #

    sites_data_for_engine = single_site_real_data_fixture #
    current_sites_config = sites_config_real #
    engine = AnalysisEngine(cfg, scenarios_real, sites_data_for_engine) #
    prix_revente_test = cfg.get("prix_vente_initial_slider_fallback", 0.10) #
    results = engine.calculate_financial_indicators(
        "Base",
        prix_revente=prix_revente_test, #
        sites_config=current_sites_config #
    ) #
    assert results is not None and "error" not in results, \
        f"Erreur lors de calculate_financial_indicators: {results.get('error') if results else 'None'}" #
    wacc_decimal_calculated = results.get("wacc_after_tax_annual") #
    wacc_pct_calculated = wacc_decimal_calculated * 100 if wacc_decimal_calculated is not None else None #
    irr_project_decimal = results.get("irr_project") #
    irr_project_pct = irr_project_decimal * 100 if irr_project_decimal is not None else None #
    npv_project = results.get("npv_project") #
    print(f"\n--- Test TRI Projet: dr={debt_ratio}, Re={cout_fp_pct}%, Rd={taux_interet_dette_pct}%, Subv={with_subvention} ---") #
    print(f"  Prix de revente fixe utilisé pour le test: {prix_revente_test:.4f} €/kWh") #
    if wacc_pct_calculated is not None: print(f"  WACC Calculé: {wacc_pct_calculated:.2f}% (Attendu: {expected_wacc_pct}%)") #
    else: print("  WACC Calculé: None") #
    if irr_project_pct is not None: print(f"  TRI Projet Calculé: {irr_project_pct:.2f}%") #
    else: print("  TRI Projet Calculé: None") #
    if npv_project is not None: print(f"  VAN Projet Calculée: {npv_project:,.0f} €") #
    else: print("  VAN Projet Calculée: None") #
    assert wacc_pct_calculated is not None, "WACC (wacc_after_tax_annual) absent des résultats" #
    assert math.isclose(wacc_pct_calculated, expected_wacc_pct, rel_tol=1e-2, abs_tol=0.05), \
        f"WACC calculé {wacc_pct_calculated:.2f}% ≠ WACC attendu {expected_wacc_pct:.2f}%" #
    assert irr_project_pct is not None, "TRI Projet (irr_project) absent ou NaN des résultats" #
    assert tri_projet_min_expected <= irr_project_pct <= tri_projet_max_expected, \
        f"TRI Projet ({irr_project_pct:.2f}%) hors de la plage attendue [{tri_projet_min_expected}%, {tri_projet_max_expected}%]" #
    if pd.notna(irr_project_decimal) and pd.notna(wacc_decimal_calculated) and pd.notna(npv_project): #
        if math.isclose(irr_project_decimal, wacc_decimal_calculated, abs_tol=1e-4): #
            assert math.isclose(npv_project, 0, abs_tol=max(1, abs(npv_project * 0.05))), \
                f"Si TRI Projet ≈ WACC, VAN Projet ({npv_project:.0f}€) devrait être proche de 0." #
        elif irr_project_decimal > wacc_decimal_calculated: #
            assert npv_project > -max(1, abs(npv_project * 0.01)), \
                f"Si TRI Projet ({irr_project_pct:.2f}%) > WACC ({wacc_pct_calculated:.2f}%), VAN Projet ({npv_project:.0f}€) devrait être > 0." #
        elif irr_project_decimal < wacc_decimal_calculated: #
            assert npv_project < max(1, abs(npv_project * 0.01)), \
                f"Si TRI Projet ({irr_project_pct:.2f}%) < WACC ({wacc_pct_calculated:.2f}%), VAN Projet ({npv_project:.0f}€) devrait être < 0." #

# -----------------------------------------------------------------------------
# Test VAN Projet avec WACC=0 (INCHANGÉ mais utilise les nouvelles fixtures)
# -----------------------------------------------------------------------------
# --- Test VAN Projet avec WACC=0 (inchangé) ---
def test_van_project_with_zero_wacc(base_config_real, scenarios_real, single_site_real_data_fixture, sites_config_real): #
    cfg = base_config_real.copy() #
    cfg.update({
        "debt_ratio": 0.0, #
        "with_loan": False, #
        "cout_fonds_propres": 0.0, #
    })
    sites_data_for_engine = single_site_real_data_fixture #
    current_sites_config = sites_config_real #
    engine = AnalysisEngine(cfg, scenarios_real, sites_data_for_engine) #
    results = engine.calculate_financial_indicators("Base", prix_revente=0.10, sites_config=current_sites_config) #
    assert results is not None and "error" not in results, \
        f"Erreur calcul indicateurs: {results.get('error') if results else 'None'}" #
    npv_project = results.get("npv_project") #
    wacc_decimal_calculated = results.get("wacc_after_tax_annual") #
    wacc_pct_calculated = wacc_decimal_calculated * 100 if wacc_decimal_calculated is not None else None #
    monthly_data_df = results.get("monthly_data") #
    assert wacc_pct_calculated is not None, "WACC (wacc_after_tax_annual) non trouvé" #
    assert math.isclose(wacc_pct_calculated, 0.0, abs_tol=1e-3), \
        f"Le WACC calculé ({wacc_pct_calculated}%) devrait être 0% pour ce test." #
    assert npv_project is not None, "npv_project non trouvé" #
    assert monthly_data_df is not None and not monthly_data_df.empty, "monthly_data absent ou vide" #
    assert "OCF_Projet" in monthly_data_df.columns, "Colonne 'OCF_Projet' manquante" #
    sum_ocf_project_mensuels = monthly_data_df["OCF_Projet"].fillna(0).sum() #
    print(f"\n--- Test VAN Projet avec WACC=0 ---") #
    print(f"  Config 'cout_fonds_propres': {cfg.get('cout_fonds_propres')}%") #
    if wacc_pct_calculated is not None: #
        print(f"  WACC Calculé: {wacc_pct_calculated:.2f}%") #
    else:
        print(f"  WACC Calculé: None") #
    print(f"  NPV Projet Calculé: {npv_project:.2f} €") #
    print(f"  Somme des OCF Projet Mensuels: {sum_ocf_project_mensuels:.2f} €") #
    assert math.isclose(npv_project, sum_ocf_project_mensuels, rel_tol=1e-3), ( #
        f"Quand WACC est 0%, VAN Projet ({npv_project:.2f} €) doit égaler la somme arithmétique "
        f"des OCF Projet mensuels ({sum_ocf_project_mensuels:.2f} €)."
    )

# -----------------------------------------------------------------------------
# NOUVEAUX TESTS BASÉS SUR LES RECOMMANDATIONS
# -----------------------------------------------------------------------------

# --- Tests LCOE Annuel Contrôlé (Corrigés) ---
@pytest.mark.parametrize("wacc_annuel, valeur_residuelle, construction_mois, expected_lcoe_exact", [
    (0.05, 0.0, 0, 0.5981707317), # WACC 5%, Pas de VR
    (0.07, 1000.0, 0, 0.5706521739), # WACC 7%, VR de 1000
]) #
def test_lcoe_annual_aggregation_controlled(
    simple_monthly_data_lcoe,
    wacc_annuel, valeur_residuelle, construction_mois, expected_lcoe_exact
): #
    """Teste calculate_lcoe_annual_aggregation avec des données contrôlées."""
    # from modules.engine_module.financial_calculations import calculate_lcoe_annual_aggregation # Déjà importé en haut

    # Pour ce test unitaire, on utilise directement la fixture de données mensuelles
    # et on ne passe pas par AnalysisEngine complet.
    # On simule que le CAPEX dans simple_monthly_data_lcoe est déjà celui à utiliser pour T0.
    
    # Adaptation pour que le CAPEX soit bien en T0 de la phase d'exploitation LCOE
    # La fixture simple_monthly_data_lcoe met déjà le CAPEX au premier mois,
    # et comme construction_mois=0 est passé, cela devrait fonctionner.
    
    lcoe_calculated = calculate_lcoe_annual_aggregation(
        wacc_annual_discount_rate=wacc_annuel, #
        monthly_df_results=simple_monthly_data_lcoe, #
        terminal_value_net_project=valeur_residuelle, #
        construction_period_months=construction_mois #
    ) #
    assert lcoe_calculated is not None, "LCOE calculé ne devrait pas être None" #
    print(f"LCOE Calculé (Annuel Contrôlé): {lcoe_calculated} vs Attendu Exact: {expected_lcoe_exact}") #
    # Ajustez la tolérance ou les valeurs attendues après calcul manuel précis
    assert math.isclose(lcoe_calculated, expected_lcoe_exact, rel_tol=1e-5), \
        f"LCOE Annuel contrôlé {lcoe_calculated:.8f} ≠ Attendu exact {expected_lcoe_exact:.8f}" #

# Test pour l'ancienne fonction LCOE mensuelle (si vous voulez la garder testée)
# def test_lcoe_engineering_monthly_controlled(...):
# ... (similaire mais avec taux mensuel et appel à calculate_lcoe_engineering)


# --- Test Intérêts Capitalisés (Corrigé) ---
def test_capitalized_interest(
    base_config_real, scenarios_real # sites_config_real n'est pas utilisé directement ici
    # single_site_real_data_fixture # Remplacé par dummy_sites_data ci-dessous
    # monthly_data_construction_interest # Non utilisé comme entrée pour l'engine directement
): #
    """Vérifie le mécanisme des intérêts capitalisés."""
    cfg = base_config_real.copy() #
    cfg.update({
        "duree_construction": 3,
        "capitalize_construction_interest": True,
        "with_loan": True,
        "debt_ratio": 0.50, # 50% de dette
        "taux_interet_dette": 12.0, # 12% annuel = 1% par mois
        "capex_scenario": 12000, # CAPEX Total pour le projet de test
        "puissance_kwc_installee": 1, # Valeur non nulle pour éviter problèmes dans certaines logiques
        # Forcer l'utilisation de la config globale pour CAPEX/OPEX en passant un sites_config vide à l'engine
    })

    # Créer un dummy_sites_data pour AnalysisEngine, car il attend un dict.
    # Les données de production/consommation réelles ne sont pas critiques pour ce test spécifique.
    # On peut utiliser un DataFrame vide ou minimal.
    dummy_site_key = "site_pour_test_interets_cap" #
    dummy_hourly_data = pd.DataFrame({
        'Temps': pd.date_range(start=cfg["date_debut_ppa"], periods=24 * 31, freq='h', tz='UTC'), # Un mois de données horaires
        'production_kwh': 0.0,
        'consumption_kwh': 0.0
    }) #
    # Le AnalysisEngine s'attend à ce que 'Temps' soit déjà un datetime lors de l'appel à validate_and_prepare_sites_data
    # Mais validate_and_prepare_sites_data va le reconvertir. Passons-le comme string pour simuler une entrée brute.

    sites_data_for_engine_test = {dummy_site_key: dummy_hourly_data} #
    
    # Pour ce test, on s'assure que la config spécifique des sites est vide ou ne surdéfinit pas le CAPEX
    # afin que `cfg['capex_scenario']` soit utilisé.
    empty_sites_specific_config = {} #

    engine = AnalysisEngine(cfg, scenarios_real, sites_data_for_engine_test) #
    results = engine.calculate_financial_indicators(
        "Base",
        prix_revente=0.10, # Non critique pour ce test
        sites_config=empty_sites_specific_config # Important pour utiliser capex_scenario de cfg
    ) #
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}" #
    dfm = results["monthly_data"] #

    interets_payes_construction = dfm[dfm['Is_Construction_Phase'] == 1.0]['Interets_Payes'].sum() #
    print(f"Intérêts payés pendant construction (devraient être 0 si capitalisés): {interets_payes_construction}") #
    assert math.isclose(interets_payes_construction, 0.0, abs_tol=1e-2), \
        "Les intérêts ne devraient pas être 'payés' (décaissés) pendant la construction si capitalisés." #

    # Calcul manuel des intérêts capitalisés attendus (basé sur CAPEX de 12000, dette de 6000)
    # Le moteur répartit le capex_scenario sur la duree_construction pour les tirages.
    # CAPEX_Initial_Mensuel dans dfm est le résultat de cette répartition du capex_scenario.
    # Debt_Drawn_This_Month est calculé comme debt_ratio * CAPEX_Initial_Mensuel.
    
    # Récupérer le total de la dette effectivement tirée par le moteur pendant la construction
    total_debt_drawn_engine = dfm[dfm['Is_Construction_Phase'] == 1.0]['Debt_Drawn_This_Month'].sum() #
    
    # Recalculons les intérêts capitalisés attendus basé sur les tirages mensuels effectifs du moteur.
    # (Le calcul manuel précédent était basé sur une répartition égale, ce qui est ce que le moteur fait
    # si capex_pour_repartition_mensuelle est constant.)
    # Ici, debt_amount_total = 12000 * 0.5 = 6000.
    # debt_drawn_monthly_series.iloc[constr_month_idx] = 6000 / 3 = 2000.
    
    # Mois 1: Dette tirée = 2000. Solde pour intérêt = 2000. Intérêt capitalisé = 2000 * 0.01 = 20.
    # Mois 2: Dette tirée = 2000. Solde pour intérêt = 2000 (solde N-1 tiré) + 2000 (nouveau tirage) = 4000. Intérêt capitalisé = 4000 * 0.01 = 40.
    # Mois 3: Dette tirée = 2000. Solde pour intérêt = 4000 (solde N-1 tiré) + 2000 (nouveau tirage) = 6000. Intérêt capitalisé = 6000 * 0.01 = 60.
    # Note : Le `current_debt_drawn_balance` dans la boucle du moteur est le solde *après* tirage du mois.
    
    # Vérifions le calcul des intérêts capitalisés directement par le moteur,
    # en comparant le `final_loan_principal_for_amortization` (implicite) avec la somme des tirages.
    # Le `final_loan_principal_for_amortization` est la somme des `Principal_Rembourse` en exploitation.
    
    interets_capitalises_attendus_manual = 120.0 #
    expected_loan_to_be_repaid = total_debt_drawn_engine + interets_capitalises_attendus_manual #

    principal_amorti_total_exploitation = dfm[dfm['Is_Construction_Phase'] == 0.0]['Principal_Rembourse'].sum() #
    
    print(f"Total Dette Tirée (Moteur, construction): {total_debt_drawn_engine:.2f}") #
    print(f"Intérêts Capitalisés Attendus (Manuel, basé sur tirages moteur): {interets_capitalises_attendus_manual:.2f}") # Cet affichage est basé sur le calcul manuel qui correspond à la logique du moteur
    print(f"Principal total attendu à rembourser (Tirages Moteur + Int. Cap. Manuel): {expected_loan_to_be_repaid:.2f}") #
    print(f"Principal total remboursé en exploitation (Moteur): {principal_amorti_total_exploitation:.2f}") #

    assert math.isclose(total_debt_drawn_engine, 6000.0, rel_tol=1e-3), "Le total de la dette tirée par le moteur devrait être 6000€." #
    assert math.isclose(principal_amorti_total_exploitation, expected_loan_to_be_repaid, rel_tol=1e-3), \
        "Le principal total remboursé en exploitation ne correspond pas au total tiré + intérêts capitalisés calculés." #
    
    solde_dette_toute_fin = dfm['Solde_Dette_Fin_Mois'].iloc[-1] #
    assert math.isclose(solde_dette_toute_fin, 0.0, abs_tol=1.0), \
        f"Le solde de la dette à la toute fin de la simulation devrait être proche de zéro (obtenu: {solde_dette_toute_fin:.2f})" #

# --- Tests Inflation et Valeur Terminale (inchangés mais utilisent les nouvelles fixtures) ---
@pytest.mark.parametrize("inflation_config", [
    {"taux_inflation": 0.0, "tarif_oa_indexe_inflation": False, "turpe_indexe_inflation": False, "id": "zero_inflation"}, #
    {"taux_inflation": 2.0, "tarif_oa_indexe_inflation": True, "turpe_indexe_inflation": True, "taux_inflation_tarif_oa": 2.0, "id": "with_inflation_2pct"}, #
    # On pourrait ajouter un cas où les revenus sont fixes mais les coûts OPEX/TURPE sont indexés.
]) #
def test_inflation_impact(
    base_config_real, scenarios_real, sites_config_real, single_site_real_data_fixture,
    inflation_config
): #
    cfg = base_config_real.copy() #
    cfg.update(inflation_config) #
    # Utiliser un prix de revente qui rend le projet marginalement rentable ou non rentable
    # pour mieux voir l'impact de l'inflation sur la VAN.
    cfg["prix_vente_initial_slider_fallback"] = 0.09 # Exemple
    
    engine = AnalysisEngine(cfg, scenarios_real, single_site_real_data_fixture) #
    results = engine.calculate_financial_indicators(
        "Base", 
        prix_revente=cfg["prix_vente_initial_slider_fallback"], #
        sites_config=sites_config_real #
    ) #
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}" #
    
    npv_project = results.get("npv_project") #
    irr_project = results.get("irr_project") #
    lcoe = results.get("lcoe") #

    print(f"\n--- Test Impact Inflation ({inflation_config['id']}) ---") #
    print(f"  Taux Inflation Config: {cfg['taux_inflation']}%") #
    print(f"  VAN Projet: {npv_project:,.0f} €") #
    print(f"  TRI Projet: {irr_project*100:.2f}%" if irr_project is not None else "N/A") #
    print(f"  LCOE: {lcoe:.4f} €/kWh" if lcoe is not None else "N/A") #

    # Pour faire une assertion utile, il faudrait stocker le résultat du cas "zero_inflation"
    # et le comparer à "with_inflation_2pct".
    if not hasattr(test_inflation_impact, "results_store"): #
        test_inflation_impact.results_store = {} #
    test_inflation_impact.results_store[inflation_config['id']] = {"npv": npv_project, "irr": irr_project, "lcoe": lcoe} #

    if "zero_inflation" in test_inflation_impact.results_store and \
       "with_inflation_2pct" in test_inflation_impact.results_store and \
       inflation_config['id'] == "with_inflation_2pct": #
        res_zero_inf = test_inflation_impact.results_store["zero_inflation"] #
        res_with_inf = test_inflation_impact.results_store["with_inflation_2pct"] #
        
        # Attentes (peuvent varier selon l'indexation relative des revenus vs coûts):
        # Si les revenus sont indexés au même taux que les coûts, l'impact de l'inflation "pure" sur la VAN/TRI réel pourrait être faible.
        # Si les coûts sont indexés et pas les revenus (ou moins), la VAN/TRI devrait baisser avec l'inflation.
        # Le LCOE (nominal) devrait augmenter avec l'inflation des coûts.
        if res_zero_inf["lcoe"] is not None and res_with_inf["lcoe"] is not None: #
            print(f"  Comparaison LCOE: ZeroInf={res_zero_inf['lcoe']:.4f}, WithInf_2pct={res_with_inf['lcoe']:.4f}") #
            assert res_with_inf["lcoe"] > res_zero_inf["lcoe"] - 0.001, \
                "LCOE avec inflation devrait être plus élevé (ou similaire si tous les coûts/prod sont réels) que sans inflation." #

@pytest.mark.parametrize("valeur_residuelle_pct_config, cout_demantelement_pct_config, id_suffix", [
    (0.0, 0.0, "no_rv_no_dem"), #
    (0.10, 0.0, "rv_10_no_dem"), # 10% du CAPEX Net en VR
    (0.0, 0.05, "no_rv_dem_5"), # 5% du CAPEX Brut en coût de démantèlement
    (0.10, 0.05, "rv_10_dem_5"), #
]) #
def test_terminal_value_impact(
    base_config_real, scenarios_real, sites_config_real, single_site_real_data_fixture,
    valeur_residuelle_pct_config, cout_demantelement_pct_config, id_suffix
): #
    cfg = base_config_real.copy() #
    cfg.update({
        "valeur_residuelle_pct": valeur_residuelle_pct_config, #
        "cout_demantelement_pct": cout_demantelement_pct_config, #
        "duree_ppa": 240 # Assurer une durée standard pour la comparaison
    }) #
    
    engine = AnalysisEngine(cfg, scenarios_real, single_site_real_data_fixture) #
    results = engine.calculate_financial_indicators(
        "Base", 
        prix_revente=cfg.get("prix_vente_initial_slider_fallback", 0.10), #
        sites_config=sites_config_real #
    ) #
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}" #
    
    npv_project = results.get("npv_project") #
    irr_project = results.get("irr_project") #
    
    # La valeur terminale nette est calculée dans core_analyzer et ajoutée au dernier flux OCF Projet
    # valeur_residuelle_nette_projet = (capex_net_subvention_info * valeur_residuelle_pct_config) - \\
    #                                  (capex_brut_total_scenario * cout_demantelement_pct_config)
    # Cette valeur est déjà incluse dans la VAN Projet et l'IRR Projet.

    print(f"\n--- Test Impact Valeur Terminale ({id_suffix}) ---") #
    print(f"  Config VR%: {valeur_residuelle_pct_config*100:.0f}%, Démant%: {cout_demantelement_pct_config*100:.0f}%") #
    print(f"  VAN Projet: {npv_project:,.0f} €") #
    print(f"  TRI Projet: {irr_project*100:.2f}%" if irr_project is not None else "N/A") #

    if not hasattr(test_terminal_value_impact, "base_npv"): # Stocker le NPV du cas de base (sans RV, sans démant.)
        if id_suffix == "no_rv_no_dem": #
            test_terminal_value_impact.base_npv = npv_project #
            test_terminal_value_impact.base_irr = irr_project #

    if hasattr(test_terminal_value_impact, "base_npv"): #
        if id_suffix == "rv_10_no_dem": # Avec VR positive
            assert npv_project > test_terminal_value_impact.base_npv - 1, "VAN Projet devrait augmenter avec VR positive" #
            if irr_project is not None and test_terminal_value_impact.base_irr is not None: #
                 assert irr_project > test_terminal_value_impact.base_irr - 0.0001, "TRI Projet devrait augmenter avec VR positive" #
        elif id_suffix == "no_rv_dem_5": # Avec coût de démantèlement
            assert npv_project < test_terminal_value_impact.base_npv + 1, "VAN Projet devrait diminuer avec coût de démantèlement" #
            if irr_project is not None and test_terminal_value_impact.base_irr is not None: #
                assert irr_project < test_terminal_value_impact.base_irr + 0.0001, "TRI Projet devrait diminuer avec coût de démantèlement" #

# --- Tests pour Edge Cases (exemples à développer) ---

# --- Test WACC Rd > Re (inchangé) ---
def test_wacc_rd_greater_than_re(base_config_real): #
    """Teste le calcul du WACC quand le coût de la dette est supérieur au coût des fonds propres."""
    from modules.engine_module.financial_calculations import calculate_wacc #
    cfg = base_config_real.copy() #
    
    debt_ratio = 0.5 #
    taux_interet_dette_pct = 10.0 # Rd = 10%
    cout_fonds_propres_pct = 6.0  # Re = 6%
    taux_imposition_pct = cfg.get("taux_imposition", 25.0) #
    
    # WACC = (E/V * Re) + (D/V * Rd * (1-Tc))
    # WACC = (0.5 * 6.0) + (0.5 * 10.0 * (1 - 0.25))
    # WACC = 3.0 + (0.5 * 10.0 * 0.75)
    # WACC = 3.0 + (0.5 * 7.5)
    # WACC = 3.0 + 3.75 = 6.75 %
    expected_wacc = 6.75 #

    wacc_calculated = calculate_wacc(
        debt_ratio=debt_ratio, #
        taux_interet_dette_pct=taux_interet_dette_pct, #
        taux_imposition_pct=taux_imposition_pct, #
        cout_fonds_propres_pct=cout_fonds_propres_pct #
    ) #
    assert wacc_calculated is not None #
    print(f"\n--- Test WACC avec Rd > Re ---") #
    print(f"  Rd={taux_interet_dette_pct}%, Re={cout_fonds_propres_pct}%") #
    print(f"  WACC Calculé: {wacc_calculated:.2f}%, Attendu: {expected_wacc:.2f}%") #
    assert math.isclose(wacc_calculated, expected_wacc, rel_tol=1e-4) #

# Vous pouvez ajouter d'autres tests pour les cas limites ici
# (production nulle, WACC négatif si pertinent pour votre modèle, etc.)

# --- NOUVEAU TEST : Production Nulle une Année (Amélioré) ---
def test_zero_production_year_impact_multi_year(
    base_config_real, scenarios_real, sites_config_real, data_for_temporal_test_fixture
):
    """Teste l'impact d'une année sans production sur LCOE, VAN, TRI, avec des données multi-années."""
    cfg = base_config_real.copy()
    # Configurer pour une durée qui utilise bien les données de la fixture
    cfg.update({
        "date_debut_ppa": "2027-01-01", # Doit correspondre à data_for_temporal_test_fixture
        "duree_construction": 15,      # Doit correspondre à data_for_temporal_test_fixture
        "duree_ppa": (18 * 12) + 3,    # Doit correspondre à data_for_temporal_test_fixture
        "prix_vente_initial_slider_fallback": 0.25, # Prix très élevé pour garantir la rentabilité
        "capex_scenario": 5000.0,     # CAPEX très réduit pour être cohérent avec la production
        "puissance_kwc_installee": 10.0, # Puissance réduite
        "taux_inflation": 0.0,        # Pas d'inflation pour simplifier
        "debt_ratio": 0.0,            # 100% fonds propres pour simplifier
        "with_loan": False,           # Pas de dette
        "amortissement_duree": 5,     # Amortissement plus court
    })
    
    site_key_temporal = list(data_for_temporal_test_fixture.keys())[0]
    current_sites_config = {
        site_key_temporal: {
            'site_type': 'Producteur',
            'puissance_kwc': 10.0,      # Puissance réduite
            'capex': 5000.0,            # CAPEX très réduit
            'opex_maintenance': 50.0,   # OPEX très réduits
            'opex_insurance': 25.0,     # OPEX très réduits
            'opex_admin': 25.0,         # OPEX très réduits
            'opex_onduleur_provision_site': False
        }
    }

    # 1. Cas de Base (avec production normale)
    print(f"\n--- DÉBUT DU TEST: Production Nulle une Année ---")
    print(f"Paramètres financiers pour le test:")
    print(f"  CAPEX: {cfg['capex_scenario']} €")
    print(f"  Prix vente: {cfg['prix_vente_initial_slider_fallback']} €/kWh")
    print(f"  Puissance: {cfg['puissance_kwc_installee']} kWc")
    print(f"  OPEX total: {current_sites_config[site_key_temporal]['opex_maintenance'] + current_sites_config[site_key_temporal]['opex_insurance'] + current_sites_config[site_key_temporal]['opex_admin']} €/an")
    
    engine_base = AnalysisEngine(cfg, scenarios_real, data_for_temporal_test_fixture)
    results_base = engine_base.calculate_financial_indicators(
        "Base", 
        prix_revente=cfg["prix_vente_initial_slider_fallback"],
        sites_config=current_sites_config
    )
    assert results_base and "error" not in results_base, f"Erreur Engine (cas base): {results_base.get('error')}"
    
    # Récupération des indicateurs
    lcoe_base = results_base.get("lcoe")
    npv_project_base = results_base.get("npv_project")
    irr_project_base = results_base.get("irr_project")
    
    # Affichage détaillé pour diagnostic
    print(f"Indicateurs calculés pour le cas de base:")
    print(f"  LCOE: {lcoe_base if pd.notna(lcoe_base) else 'NaN'}")
    print(f"  VAN Projet: {npv_project_base if pd.notna(npv_project_base) else 'NaN'}")
    print(f"  TRI Projet: {irr_project_base*100 if pd.notna(irr_project_base) else 'NaN'}%")
    
    if 'monthly_data' in results_base:
        monthly_data = results_base['monthly_data']
        
        # Analyser les flux de trésorerie annuels
        for year in sorted(monthly_data.index.year.unique()):
            year_data = monthly_data[monthly_data.index.year == year]
            prod_year = year_data['Production_kWh'].sum()
            revenus_year = year_data['Revenus_Total'].sum()
            opex_year = year_data['OPEX'].sum()
            ocf_projet_year = year_data['OCF_Projet'].sum()
            print(f"  Année {year}: Production={prod_year:.0f} kWh, Revenus={revenus_year:.0f} €, OPEX={opex_year:.0f} €, OCF Projet={ocf_projet_year:.0f} €")
        
        # Analyser les colonnes utilisées pour calculer VAN et TRI
        if pd.isna(npv_project_base) or pd.isna(irr_project_base):
            print(f"  ATTENTION: VAN ou TRI est NaN. Analyse des flux annuels pour IRR/NPV:")
            yearly_ocf = monthly_data.groupby(monthly_data.index.year)['OCF_Projet'].sum()
            
            # Reconstruire les flux annuels tels qu'utilisés pour le calcul du TRI
            print(f"  Flux annuels pour calcul TRI: {yearly_ocf.to_dict()}")
            
            # Vérifier s'il y a au moins un changement de signe dans les flux (requis pour TRI)
            sign_changes = (yearly_ocf.shift(1) * yearly_ocf < 0).sum()
            if sign_changes == 0:
                print(f"  PROBLÈME: Aucun changement de signe dans les flux annuels, TRI non calculable")
            
            # Calculer manuellement pour vérifier
            from scipy import optimize
            
            def npv_func(rate, cashflows, years):
                return sum(cf / (1 + rate) ** (y - years[0]) for y, cf in zip(years, cashflows))
            
            def irr_func(rate, cashflows, years):
                return npv_func(rate, cashflows, years)
            
            years = yearly_ocf.index.tolist()
            cashflows = yearly_ocf.values.tolist()
            
            try:
                # Essayer de calculer le TRI manuellement
                irr_manual = optimize.newton(lambda r: npv_func(r, cashflows, years), x0=0.1)
                print(f"  TRI calculé manuellement: {irr_manual*100:.2f}%")
            except:
                print(f"  ÉCHEC: Calcul manuel du TRI a échoué, flux probablement sans solution")
    
    # Cette assertion doit passer pour continuer le test
    # Si elle échoue, c'est que les paramètres financiers doivent encore être ajustés
    if not all(pd.notna(x) for x in [lcoe_base, npv_project_base, irr_project_base]):
        print("ÉCHEC DU TEST: Au moins un indicateur de base est NaN.")
        print("Ajustez les paramètres financiers pour garantir que tous les indicateurs soient calculables.")
        assert all(pd.notna(x) for x in [lcoe_base, npv_project_base, irr_project_base]), "Indicateurs de base non valides"

    # 2. Cas avec une année de production nulle - NOUVELLE IMPLÉMENTATION
    # Créer une copie PROFONDE pour la modification
    site_data_modified_for_zero_prod = copy.deepcopy(data_for_temporal_test_fixture)
    key_to_modify = list(site_data_modified_for_zero_prod.keys())[0]
    df_to_actually_modify = site_data_modified_for_zero_prod[key_to_modify] # Référence au DataFrame dans le dict

    # S'assurer que la colonne Temps est de type datetime pour la modification
    if not pd.api.types.is_datetime64_any_dtype(df_to_actually_modify['Temps']):
        df_to_actually_modify['Temps'] = pd.to_datetime(df_to_actually_modify['Temps'], errors='coerce')
        df_to_actually_modify.dropna(subset=['Temps'], inplace=True)
        if df_to_actually_modify.empty:
            pytest.skip("Échec conversion temps pour la modification dans test_zero_production_year_impact_multi_year")

    date_debut_exploitation_dt = pd.to_datetime(cfg["date_debut_ppa"])
    year_to_modify = date_debut_exploitation_dt.year + 1

    # Utiliser une colonne temporaire pour le masque booléen basé sur l'année
    df_to_actually_modify['year_for_filter'] = pd.to_datetime(df_to_actually_modify['Temps']).dt.year
    year_mask = (df_to_actually_modify['year_for_filter'] == year_to_modify)
    
    original_sum_prod_year_to_modify = df_to_actually_modify.loc[year_mask, 'production_kwh'].sum()

    if original_sum_prod_year_to_modify > 0:
        # Stocker la valeur originale avant modification pour vérification
        print(f"\nDIAGNOSTIC: Modifiant production pour l'année {year_to_modify}")
        print(f"  Nombre d'entrées à modifier: {year_mask.sum()}")
        print(f"  Somme production originale: {original_sum_prod_year_to_modify:.2f} kWh")
        
        # Modifier la production pour cette année à 0
        df_to_actually_modify.loc[year_mask, 'production_kwh'] = 0.0
        
        # Vérifier que la modification a bien été effectuée
        modified_sum_prod_year_to_modify = df_to_actually_modify.loc[year_mask, 'production_kwh'].sum()
        print(f"  Somme production après modification: {modified_sum_prod_year_to_modify:.2f} kWh")
        
        assert math.isclose(modified_sum_prod_year_to_modify, 0.0), \
            "La production de l'année modifiée devrait être nulle."
    else:
        pytest.skip(f"Pas de production à modifier pour l'année {year_to_modify} dans la fixture de données.")
    
    # Nettoyer la colonne temporaire
    df_to_actually_modify.drop(columns=['year_for_filter'], inplace=True)
    
    # Vérification supplémentaire des données modifiées avant de les passer à l'engine
    verify_modified = df_to_actually_modify.copy()
    if not pd.api.types.is_datetime64_any_dtype(verify_modified['Temps']):
        verify_modified['year'] = pd.to_datetime(verify_modified['Temps']).dt.year
    else:
        verify_modified['year'] = verify_modified['Temps'].dt.year
    
    prod_by_year = verify_modified.groupby('year')['production_kwh'].sum()
    print("\nVérification finale des données modifiées par année:")
    for year, prod in prod_by_year.items():
        print(f"  Année {year}: Production = {prod:.2f} kWh" + (" (MODIFIÉE)" if year == year_to_modify else ""))
    
    # Créer une nouvelle instance d'AnalysisEngine avec les données modifiées
    engine_zero_prod = AnalysisEngine(cfg, scenarios_real, site_data_modified_for_zero_prod)
    results_zero_prod = engine_zero_prod.calculate_financial_indicators(
        "Base", 
        prix_revente=cfg["prix_vente_initial_slider_fallback"],
        sites_config=current_sites_config
    )
    assert results_zero_prod and "error" not in results_zero_prod, f"Erreur Engine (cas prod nulle): {results_zero_prod.get('error')}"

    lcoe_zero_prod = results_zero_prod.get("lcoe")
    npv_project_zero_prod = results_zero_prod.get("npv_project")
    irr_project_zero_prod = results_zero_prod.get("irr_project")
    assert all(pd.notna(x) for x in [lcoe_zero_prod, npv_project_zero_prod, irr_project_zero_prod]), \
        "Indicateurs pour cas production nulle non valides"

    # NOUVEAU: Analyse détaillée des agrégations annuelles pour diagnostic
    print("\n--- ANALYSE DÉTAILLÉE DES AGRÉGATIONS ANNUELLES ---")
    years_to_check = [year_to_modify - 1, year_to_modify, year_to_modify + 1]
    for year_to_check in years_to_check:
        print(f"\n--- Année {year_to_check} ---")
        
        # Analyser le cas base
        if 'monthly_data' in results_base:
            base_year_data = results_base['monthly_data'][results_base['monthly_data'].index.year == year_to_check]
            if not base_year_data.empty:
                base_prod = base_year_data['Production_kWh'].sum()
                base_opex = base_year_data['OPEX'].sum()
                base_turpe = base_year_data.get('TURPE', pd.Series(0, index=base_year_data.index)).sum()
                base_revenus = base_year_data['Revenus_Total'].sum()
                base_ocf = base_year_data['OCF_Projet'].sum()
                
                print(f"  CAS BASE: Production={base_prod:.0f} kWh, OPEX={base_opex:.0f} €, TURPE={base_turpe:.0f} €, Revenus={base_revenus:.0f} €, OCF={base_ocf:.0f} €")
        
        # Analyser le cas avec production nulle pour une année
        if 'monthly_data' in results_zero_prod:
            zero_prod_year_data = results_zero_prod['monthly_data'][results_zero_prod['monthly_data'].index.year == year_to_check]
            if not zero_prod_year_data.empty:
                zero_prod = zero_prod_year_data['Production_kWh'].sum()
                zero_opex = zero_prod_year_data['OPEX'].sum()
                zero_turpe = zero_prod_year_data.get('TURPE', pd.Series(0, index=zero_prod_year_data.index)).sum()
                zero_revenus = zero_prod_year_data['Revenus_Total'].sum()
                zero_ocf = zero_prod_year_data['OCF_Projet'].sum()
                
                print(f"  CAS PROD NULLE: Production={zero_prod:.0f} kWh, OPEX={zero_opex:.0f} €, TURPE={zero_turpe:.0f} €, Revenus={zero_revenus:.0f} €, OCF={zero_ocf:.0f} €")
                
                # Vérifier si les OPEX/TURPE sont liés à la production
                if year_to_check == year_to_modify:
                    if math.isclose(zero_prod, 0.0) and math.isclose(zero_opex, base_opex):
                        print(f"  DIAGNOSTIC: Les OPEX ({zero_opex:.0f} €) restent constants même quand la production est nulle")
                    elif math.isclose(zero_prod, 0.0) and zero_opex < base_opex:
                        print(f"  DIAGNOSTIC: Les OPEX diminuent quand la production est nulle ({zero_opex:.0f} vs {base_opex:.0f} €)")
                    
                    if math.isclose(zero_prod, 0.0) and math.isclose(zero_turpe, base_turpe):
                        print(f"  DIAGNOSTIC: Le TURPE ({zero_turpe:.0f} €) reste constant même quand la production est nulle")

    # Calcul et affichage des totaux pour analyse du LCOE
    print("\n--- TOTAUX SUR LA DURÉE DU PROJET POUR ANALYSE LCOE ---")
    
    # Extraire les données mensuelles des deux résultats pour l'analyse LCOE
    df_base = results_base.get('monthly_data')
    df_zero_prod = results_zero_prod.get('monthly_data')
    
    if df_base is not None and df_zero_prod is not None:
        # Totaux pour le cas de base
        total_prod_base = df_base['Production_kWh'].sum()
        total_costs_base = df_base['OPEX'].sum() + df_base.get('TURPE', pd.Series(0, index=df_base.index)).sum()
        
        # Totaux pour le cas avec une année de production nulle
        total_prod_zero = df_zero_prod['Production_kWh'].sum()
        total_costs_zero = df_zero_prod['OPEX'].sum() + df_zero_prod.get('TURPE', pd.Series(0, index=df_zero_prod.index)).sum()
        
        print(f"  CAS BASE: Production totale={total_prod_base:.0f} kWh, Coûts totaux={total_costs_base:.0f} €")
        print(f"  CAS PROD NULLE: Production totale={total_prod_zero:.0f} kWh, Coûts totaux={total_costs_zero:.0f} €")
        
        print(f"  DIAGNOSTIC LCOE SIMPLIFIÉ: Ratio Coûts/Production Base={total_costs_base/total_prod_base:.4f} €/kWh vs Prod Nulle={total_costs_zero/total_prod_zero:.4f} €/kWh")
        
        # Calcul simplifié du pourcentage de production perdue vs pourcentage de coûts évités
        pct_prod_perdue = (total_prod_base - total_prod_zero) / total_prod_base * 100
        pct_couts_evites = (total_costs_base - total_costs_zero) / total_costs_base * 100
        
        print(f"  % Production perdue: {pct_prod_perdue:.2f}% vs % Coûts évités: {pct_couts_evites:.2f}%")
        print(f"  Si % Coûts évités ≈ % Production perdue, le LCOE reste stable")
        print(f"  Si % Coûts évités < % Production perdue, le LCOE augmente")
        print(f"  Si % Coûts évités > % Production perdue, le LCOE diminue")
    
    print(f"\n--- Test Production Nulle Année {year_to_modify} ---")
    print(f"  Cas Base        : LCOE={lcoe_base:.4f}, VAN={npv_project_base:,.0f}, TRI={irr_project_base*100:.2f}%")
    print(f"  Cas Prod. Nulle : LCOE={lcoe_zero_prod:.4f}, VAN={npv_project_zero_prod:,.0f}, TRI={irr_project_zero_prod*100:.2f}%")

    # MODIFIÉ: Adaptation de l'assertion selon le diagnostic des coûts
    # Si les OPEX/TURPE sont constants même quand la production est nulle (coûts fixes),
    # le LCOE devrait augmenter.
    # Si les OPEX/TURPE diminuent proportionnellement à la production (coûts variables),
    # le LCOE pourrait rester stable.
    
    # Déterminer si les coûts sont principalement fixes ou variables
    df_base_year = df_base[df_base.index.year == year_to_modify]
    df_zero_year = df_zero_prod[df_zero_prod.index.year == year_to_modify]
    
    base_year_opex_turpe = df_base_year['OPEX'].sum() + df_base_year.get('TURPE', pd.Series(0, index=df_base_year.index)).sum()
    zero_year_opex_turpe = df_zero_year['OPEX'].sum() + df_zero_year.get('TURPE', pd.Series(0, index=df_zero_year.index)).sum()
    
    costs_ratio = zero_year_opex_turpe / base_year_opex_turpe if base_year_opex_turpe > 0 else 1.0
    
    print(f"  Ratio coûts année production nulle/base: {costs_ratio:.2f}")
    
    if costs_ratio > 0.9:  # Les coûts sont principalement fixes (>90% restent même sans production)
        print("  DIAGNOSTIC: Coûts principalement fixes => Le LCOE devrait augmenter")
        assert lcoe_zero_prod > lcoe_base, "LCOE avec une année de production nulle devrait être plus élevé avec des coûts fixes."
    else:  # Les coûts sont principalement variables
        print("  DIAGNOSTIC: Coûts principalement variables => Le LCOE pourrait rester stable")
        assert math.isclose(lcoe_zero_prod, lcoe_base, rel_tol=0.05) or lcoe_zero_prod > lcoe_base, \
            "LCOE avec une année de production nulle devrait être similaire ou plus élevé."

    assert npv_project_zero_prod < npv_project_base, "VAN Projet avec une année de production nulle devrait être plus basse."
    assert irr_project_zero_prod < irr_project_base, "TRI Projet avec une année de production nulle devrait être plus bas."

# --- NOUVEAU TEST : Temporalité (Construction/Exploitation Décalées) ---
def test_temporality_construction_exploitation_offset_NEW(
    base_config_real, scenarios_real, sites_config_real, data_for_temporal_test_fixture
):
    """Teste un scénario avec construction et exploitation décalées."""
    cfg = base_config_real.copy()
    # Définir une date de début PPA et une durée de construction pour le test
    date_debut_ppa_test = "2027-01-15" # Exemple milieu de mois
    duree_construction_test = 15 # mois
    duree_ppa_test = (18 * 12) + 3 # 18 ans et 3 mois
    
    cfg.update({
        "date_debut_ppa": date_debut_ppa_test,
        "duree_construction": duree_construction_test,
        "duree_ppa": duree_ppa_test,
        "capex_scenario": 75000, # Adapter si besoin pour ce test
        "puissance_kwc_installee": 50, # Adapter si besoin
    })

    site_key_temporal = list(data_for_temporal_test_fixture.keys())[0]
    
    # Utiliser la config de site chargée du JSON, mais adapter le CAPEX/Puissance si différent
    # S'assurer que la clé du site dans data_for_temporal_test_fixture
    # correspond à une clé dans sites_config_real si on veut utiliser cette dernière.
    # Ici, on prend la première config de site du JSON et on l'adapte.
    default_site_key_from_json = list(sites_config_real.keys())[0]
    specific_site_cfg_temporal = sites_config_real.get(default_site_key_from_json, {}).copy()
    specific_site_cfg_temporal.update({ # Surcharger avec les valeurs de la config globale pour ce test
        'capex': cfg["capex_scenario"],
        'puissance_kwc': cfg["puissance_kwc_installee"],
        'opex_maintenance': cfg.get("opex_maintenance_fallback", specific_site_cfg_temporal.get('opex_maintenance', 250)),
        'opex_insurance': cfg.get("opex_insurance_fallback", specific_site_cfg_temporal.get('opex_insurance',150)),
        'opex_admin': cfg.get("opex_admin_fallback", specific_site_cfg_temporal.get('opex_admin',150)),
        'opex_onduleur_provision_site': False
    })
    current_sites_config_for_test = {site_key_temporal: specific_site_cfg_temporal}

    engine = AnalysisEngine(cfg, scenarios_real, data_for_temporal_test_fixture)
    results = engine.calculate_financial_indicators(
        "Base",
        prix_revente=cfg.get("prix_vente_initial_slider_fallback", 0.12),
        sites_config=current_sites_config_for_test
    )
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}"

    df_monthly = results.get("monthly_data")
    assert df_monthly is not None and not df_monthly.empty

    print(f"\n--- Test Temporalité Décalée (Fixture: {site_key_temporal}) ---")
    print(f"  Date début PPA (config): {cfg['date_debut_ppa']}")
    print(f"  Durée construction (config): {cfg['duree_construction']} mois")
    print(f"  Date début simulation effective (calculée par engine): {results.get('date_debut_simulation_effective')}")
    print(f"  Date début opérations (calculée par engine): {results.get('date_debut_operations')}")


    num_construction_months_results = df_monthly['Is_Construction_Phase'].sum()
    num_exploitation_months_results = len(df_monthly) - num_construction_months_results

    assert math.isclose(num_construction_months_results, cfg['duree_construction'], abs_tol=0.1), \
        f"Nombre de mois de construction ({num_construction_months_results}) ne correspond pas à config ({cfg['duree_construction']})."
    
    assert math.isclose(num_exploitation_months_results, cfg['duree_ppa'], abs_tol=0.1), \
        f"Nombre de mois d'exploitation ({num_exploitation_months_results}) ne correspond pas à config ({cfg['duree_ppa']})."
        
    # Vérifier la première date d'exploitation
    if num_exploitation_months_results > 0:
        first_op_date_results = df_monthly[df_monthly['Is_Construction_Phase'] == 0.0].index.min()
        expected_first_op_date_config = pd.to_datetime(cfg['date_debut_ppa'])
        
        # L'index de df_monthly est en fin de mois. La date de début PPA est un jour.
        # On vérifie que le premier mois d'exploitation (fin de mois) correspond bien au mois/année de date_debut_ppa.
        assert first_op_date_results.year == expected_first_op_date_config.year and \
               first_op_date_results.month == expected_first_op_date_config.month, \
               f"Premier mois d'exploitation ({first_op_date_results.strftime('%Y-%m')}) " \
               f"ne correspond pas au mois/année de début PPA configuré ({expected_first_op_date_config.strftime('%Y-%m')})."
    
    # Vérifier que les indicateurs sont calculés
    assert pd.notna(results.get("npv_project")), "VAN Projet ne devrait pas être NaN pour test temporalité"
    assert pd.notna(results.get("irr_project")), "TRI Projet ne devrait pas être NaN pour test temporalité"
    assert pd.notna(results.get("lcoe")), "LCOE ne devrait pas être NaN pour test temporalité"

# --- NOUVEAU TEST : Production Totalement Nulle sur la Durée ---
def test_lcoe_with_total_zero_production(
    base_config_real, scenarios_real, sites_config_real, data_for_temporal_test_fixture
):
    """Teste le calcul du LCOE quand la production totale sur la durée est nulle."""
    cfg = base_config_real.copy()
    cfg.update({
        "date_debut_ppa": "2027-01-01",
        "duree_construction": 6, # Réduit pour ce test
        "duree_ppa": 60,        # Réduit pour ce test
    })
    
    # Modifier les données pour avoir une production nulle sur toute la durée
    site_data_zero_prod = copy.deepcopy(data_for_temporal_test_fixture)
    site_key = list(site_data_zero_prod.keys())[0]
    df_site = site_data_zero_prod[site_key].copy()
    # Forcer toute la production à zéro
    df_site['production_kwh'] = 0.0 
    site_data_zero_prod[site_key] = df_site

    # Adapter la config de site pour ce test
    default_site_key_from_json = list(sites_config_real.keys())[0]
    specific_site_cfg = sites_config_real.get(default_site_key_from_json, {}).copy()
    specific_site_cfg.update({
        'capex': cfg.get("capex_scenario", 50000),
        'puissance_kwc': cfg.get("puissance_kwc_installee", 45),
        'opex_maintenance': cfg.get("opex_maintenance_fallback", 200),
        'opex_insurance': cfg.get("opex_insurance_fallback", 100),
        'opex_admin': cfg.get("opex_admin_fallback", 100),
    })
    current_sites_config = {site_key: specific_site_cfg}

    engine = AnalysisEngine(cfg, scenarios_real, site_data_zero_prod)
    results = engine.calculate_financial_indicators(
        "Base",
        prix_revente=0.10, # Prix non critique ici
        sites_config=current_sites_config
    )
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}"
    
    lcoe = results.get("lcoe")
    print(f"\n--- Test LCOE avec Production Totale Nulle ---")
    print(f"  LCOE Calculé: {lcoe}")

    # LCOE devrait être NaN car la NPV de la production sera nulle
    # La fonction calculate_lcoe_annual_aggregation retourne np.nan dans ce cas.
    assert pd.isna(lcoe), "LCOE devrait être NaN si la production totale est nulle."

# --- Tests d'Échec (pytest.raises) ---
def test_invalid_wacc_input_for_lcoe(simple_monthly_data_lcoe):
    """Teste que LCOE gère un WACC invalide (ex: None)."""
    from modules.engine_module.financial_calculations import calculate_lcoe_annual_aggregation
    # La fonction retourne np.nan si wacc_annual_discount_rate est None ou invalide,
    # elle ne lève pas d'exception elle-même pour cela, mais log un warning.
    # Donc, on vérifie le retour NaN.
    lcoe = calculate_lcoe_annual_aggregation(
        wacc_annual_discount_rate=None, # WACC invalide
        monthly_df_results=simple_monthly_data_lcoe,
        terminal_value_net_project=0.0,
        construction_period_months=0
    )
    print(f"\n--- Test LCOE avec WACC Invalide (None) ---")
    print(f"  LCOE Calculé: {lcoe}")
    assert pd.isna(lcoe), "LCOE devrait être NaN avec un WACC=None."

    lcoe_invalid_rate = calculate_lcoe_annual_aggregation(
        wacc_annual_discount_rate=-2.0, # WACC invalide (< -1)
        monthly_df_results=simple_monthly_data_lcoe,
        terminal_value_net_project=0.0,
        construction_period_months=0
    )
    print(f"--- Test LCOE avec WACC Invalide (-2.0) ---")
    print(f"  LCOE Calculé: {lcoe_invalid_rate}")
    assert pd.isna(lcoe_invalid_rate), "LCOE devrait être NaN avec un WACC < -1."


def test_engine_initialization_errors():
    """Teste que AnalysisEngine lève des TypeError pour des inputs invalides."""
    with pytest.raises(TypeError, match="config doit être un dict"):
        AnalysisEngine(config="not a dict", scenarios={}, sites_data={})
    
    with pytest.raises(TypeError, match="scenarios doit être un dict"):
        AnalysisEngine(config={}, scenarios="not a dict", sites_data={})
        
    with pytest.raises(TypeError, match="sites_data doit être un dict"):
        AnalysisEngine(config={}, scenarios={}, sites_data="not a dict")

# -----------------------------------------------------------------------------
# Test "Golden Sample" - Comparaison avec un modèle Excel contrôlé
# -----------------------------------------------------------------------------

@pytest.fixture(scope="function")
def golden_sample_config(base_config_real):
    """Configuration pour le test 'Golden Sample' basée sur un modèle Excel simplifié."""
    cfg = base_config_real.copy()
    cfg.update({
        "date_debut_ppa": "2025-01-01",
        "duree_ppa": 36,  # 3 ans pour cet exemple
        "duree_construction": 0,
        "capex_scenario": 100000.0, # Correspond au CAPEX total pour UN site
        "puissance_kwc_installee": 50.0, # Utilisé pour calculer la subvention (ici nulle) et TURPE
        
        "subvention_rate_le3": 0.0, # Pas de subvention
        "subvention_rate_le9": 0.0,
        "subvention_rate_le36": 0.0,
        "subvention_rate_le100": 0.0,
        "subvention_rate_le500": 0.0,
        
        "taux_inflation": 0.0, # Pas d'inflation
        "tarif_oa_indexe_inflation": False,
        "turpe_indexe_inflation": False,
        
        "with_loan": False, # 100% Fonds Propres
        "debt_ratio": 0.0,
        "taux_interet_dette": 0.0,
        "debt_term_years": 0,
        
        "amortissement_duree": 10,
        "valeur_residuelle_pct": 0.0,
        "cout_demantelement_pct": 0.0,
        
        "cout_fonds_propres": 8.0, # Pour WACC et actualisation VAN
        "prix_vente_initial_slider_fallback": 0.15, # Prix de vente utilisé
        "source_prix_autoconso": "prix_initial", # Assure que le prix de vente est utilisé pour l'autoconsommation
        
        # OPEX et TURPE globaux (seront utilisés si sites_config est vide ou ne les surdéfinit pas)
        "opex_maintenance_fallback": 0, # Sera défini par sites_config
        "opex_insurance_fallback": 0,
        "opex_admin_fallback": 0,
        "opex_onduleur_provision_globale": False,
        # TURPE sera calculé, mais avec inflation 0, il sera constant.
        # La config de base_config_real pour TURPE sera utilisée.
    })
    return cfg

@pytest.fixture(scope="function")
def golden_sample_sites_config():
    """Configuration des sites pour le test 'Golden Sample'."""
    # Configuration pour UN seul site correspondant au Golden Sample
    return {
        "golden_site_1": {
            'site_type': 'Producteur', # Important
            'puissance_kwc': 50.0,
            'capex': 100000.0,
            'opex_maintenance': 1000.0 / 3.0 * 0.4, # Exemple de répartition si OPEX totaux = 1000
            'opex_insurance': 1000.0 / 3.0 * 0.3,
            'opex_admin': 1000.0 / 3.0 * 0.3,
            'opex_onduleur_provision_site': False,
            # 'opex_onduleur_total_cost_site': 0, (ignorer si provision = False)
            # 'opex_onduleur_lifetime_site': 0,  (ignorer si provision = False)
        }
    }

@pytest.fixture(scope="function")
def golden_sample_sites_data():
    """Données de production/consommation pour le test 'Golden Sample'."""
    # Crée les données de production/consommation mensuelles constantes pour 3 ans
    # Doit correspondre aux hypothèses du Golden Sample Excel
    start_date = pd.to_datetime("2025-01-01")
    num_months = 36 # 3 ans
    
    # Générer un index horaire pour 3 ans
    # Pour que aggregate_energy_data fonctionne, il faut des données horaires.
    # validate_and_prepare_sites_data va aussi parser 'Temps'.
    hourly_index = pd.date_range(start=start_date, periods=num_months * 30 * 24, freq='h') # Approximation
    
    df = pd.DataFrame(index=hourly_index)
    df['Temps'] = df.index.strftime('%Y-%m-%d %H:%M:%S') 
    
    # Production horaire constante pour atteindre 55000 kWh/an (55000 / (365*24))
    # Consommation horaire constante pour atteindre 30000 kWh/an (30000 / (365*24))
    # Pour que aggregate_energy_data fonctionne bien, nous générons des données 
    # horaires qui, une fois agrégées, donnent les bons totaux mensuels.
    
    # Production Annuelle Cible: 55000 kWh -> Mensuel: 55000/12 = 4583.33 kWh
    # Consommation Annuelle Cible: 30000 kWh -> Mensuel: 30000/12 = 2500 kWh
    # Pour un mois de 30 jours * 24 heures = 720 heures
    hourly_prod_rate = (55000.0 / 12.0) / (30.0 * 24.0)
    hourly_cons_rate = (30000.0 / 12.0) / (30.0 * 24.0)

    df['production_kwh'] = hourly_prod_rate
    df['consumption_kwh'] = hourly_cons_rate
    
    return {"golden_site_1": df[['Temps', 'production_kwh', 'consumption_kwh']]}

def test_golden_sample_comparison(
    golden_sample_config, 
    scenarios_real, # Utiliser le scénario "Base"
    golden_sample_sites_config,
    golden_sample_sites_data
):
    """
    Test qui compare les résultats du moteur AnalysisEngine avec un modèle Excel de référence.
    Le 'Golden Sample' est un cas simplifié et contrôlé permettant de valider les calculs du moteur.
    """
    cfg = golden_sample_config
    
    # IMPORTANT: Vérification explicite des paramètres clés pour alignement avec Excel
    print(f"\n--- Test Golden Sample - VÉRIFICATION DES PARAMÈTRES CLÉS ---")
    print(f"  Date début PPA: {cfg['date_debut_ppa']}")
    print(f"  Durée PPA: {cfg['duree_ppa']} mois")
    print(f"  Durée construction: {cfg['duree_construction']} mois (DOIT ÊTRE 0 POUR ALIGNEMENT EXCEL SIMPLE)")
    print(f"  CAPEX: {cfg['capex_scenario']} €")
    print(f"  Prix Vente: {cfg['prix_vente_initial_slider_fallback']} €/kWh")
    print(f"  Source prix autoconso: {cfg.get('source_prix_autoconso', 'Non spécifié')} (doit être 'prix_initial')")
    print(f"  WACC (Fonds Propres): {cfg['cout_fonds_propres']}%")
    print(f"  Dette: {cfg['with_loan']} (ratio: {cfg['debt_ratio']})")
    print(f"  Amortissement: Linéaire sur {cfg['amortissement_duree']} ans")
    print(f"  Inflation: {cfg['taux_inflation']}% (tarifs indexés: {cfg.get('tarif_oa_indexe_inflation', False)})")
    print(f"  Subvention: {cfg['subvention_rate_le3']}%, {cfg['subvention_rate_le9']}%, {cfg['subvention_rate_le36']}%, {cfg['subvention_rate_le100']}%, {cfg['subvention_rate_le500']}%")
    
    # Vérification des données de sites
    site_key = list(golden_sample_sites_data.keys())[0]
    df_site = golden_sample_sites_data[site_key]
    
    # Somme des données pour vérifier les totaux annuels
    if 'production_kwh' in df_site.columns and 'consumption_kwh' in df_site.columns:
        # Convertir 'Temps' en datetime s'il ne l'est pas déjà
        if not pd.api.types.is_datetime64_any_dtype(df_site['Temps']):
            temps_dt = pd.to_datetime(df_site['Temps'])
        else:
            temps_dt = df_site['Temps']
        
        # Créer un DataFrame avec les dates pour l'analyse
        df_analysis = pd.DataFrame({
            'year': temps_dt.dt.year,
            'month': temps_dt.dt.month,
            'production_kwh': df_site['production_kwh'],
            'consumption_kwh': df_site['consumption_kwh']
        })
        
        # Calculer les totaux mensuels pour vérification
        monthly_totals = df_analysis.groupby(['year', 'month']).agg({
            'production_kwh': 'sum',
            'consumption_kwh': 'sum'
        }).reset_index()
        
        # Afficher les premiers mois pour vérification
        print("\n  Vérification des données mensuelles (premiers 3 mois):")
        for i in range(min(3, len(monthly_totals))):
            year, month = monthly_totals.iloc[i]['year'], monthly_totals.iloc[i]['month']
            prod = monthly_totals.iloc[i]['production_kwh']
            cons = monthly_totals.iloc[i]['consumption_kwh']
            print(f"  {int(year)}-{int(month):02d}: Production={prod:.2f} kWh, Consommation={cons:.2f} kWh")
        
        # Calculer et afficher les totaux annuels
        yearly_totals = df_analysis.groupby('year').agg({
            'production_kwh': 'sum',
            'consumption_kwh': 'sum'
        })
        
        print("\n  Totaux annuels pour Excel:")
        for year, row in yearly_totals.iterrows():
            print(f"  {year}: Production={row['production_kwh']:.0f} kWh, Consommation={row['consumption_kwh']:.0f} kWh")
            
        # Vérifier si les totaux correspondent aux attentes du Golden Sample
        total_prod = yearly_totals['production_kwh'].sum()
        total_cons = yearly_totals['consumption_kwh'].sum()
        print(f"\n  TOTAL SUR DURÉE: Production={total_prod:.0f} kWh, Consommation={total_cons:.0f} kWh")
        print(f"  --> Valeurs cibles annuelles: Production=55000 kWh/an, Consommation=30000 kWh/an")
        print(f"  --> Sur {cfg['duree_ppa']/12:.1f} ans: Production cible={55000*(cfg['duree_ppa']/12):.0f} kWh, Consommation cible={30000*(cfg['duree_ppa']/12):.0f} kWh")
    
    # Exécution du moteur de calcul
    engine = AnalysisEngine(cfg, scenarios_real, golden_sample_sites_data)
    results = engine.calculate_financial_indicators(
        "Base", # Utiliser le scénario de base (pas de modificateurs)
        prix_revente=cfg.get("prix_vente_initial_slider_fallback"), # Utilise 0.15 €/kWh
        sites_config=golden_sample_sites_config 
    )
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}"

    df_monthly_engine = results.get("monthly_data")
    assert df_monthly_engine is not None and not df_monthly_engine.empty

    # --- EXPORT CSV DES FLUX DU MOTEUR ---
    export_filename = "golden_sample_engine_cashflows.csv"
    df_monthly_engine.to_csv(export_filename)
    print(f"\nFlux mensuels du moteur exportés vers: {os.path.abspath(export_filename)}")
    
    # --- AFFICHAGE DES PREMIERS MOIS POUR DÉBOGAGE ---
    print("\nAperçu des premiers mois de flux (pour alignement avec Excel):")
    premiers_mois = min(3, len(df_monthly_engine))
    columns_to_show = ['Revenus_Total', 'OPEX', 'TURPE', 'Amortissement', 'EBITDA', 'EBIT', 'EBT', 'Total_IS_Decaisse_Mois', 'Resultat_Net', 'OCF_Projet']
    
    for i in range(premiers_mois):
        date_mois = df_monthly_engine.index[i]
        print(f"\nMois {i+1} ({date_mois.strftime('%Y-%m')}):")
        for col in columns_to_show:
            value = df_monthly_engine.iloc[i].get(col, 'Non disponible')
            print(f"  {col}: {value if pd.notna(value) else 'NaN'}")
    
    # --- ANALYSE DES AGRÉGATS ANNUELS ---
    print("\nAgrégats annuels pour vérification avec Excel:")
    df_monthly_engine['year'] = df_monthly_engine.index.year
    yearly_aggregates = df_monthly_engine.groupby('year').agg({
        'Revenus_Total': 'sum',
        'OPEX': 'sum',
        'TURPE': 'sum',
        'Production_kWh': 'sum',
        'Amortissement': 'sum',
        'EBITDA': 'sum',
        'EBIT': 'sum',
        'EBT': 'sum',
        'Total_IS_Decaisse_Mois': 'sum',
        'Resultat_Net': 'sum',
        'OCF_Projet': 'sum'
    })
    
    for year, row in yearly_aggregates.iterrows():
        print(f"\nAnnée {year}:")
        for col in yearly_aggregates.columns:
            print(f"  {col}: {row[col]:,.2f}")
    
    # --- RÉCUPÉRATION DES INDICATEURS DU MOTEUR ---
    engine_van_projet = results.get("npv_project")
    engine_tri_projet = results.get("irr_project") # Est en décimal
    engine_lcoe = results.get("lcoe")
    engine_payback_projet = results.get("payback_project")

    # --- VALEURS CALCULÉES PAR EXCEL (À RENSEIGNER MANUELLEMENT APRÈS CALCUL DANS EXCEL) ---
    # IMPORTANT: Vous devez mettre à jour ces valeurs avec celles de votre Excel Golden Sample
    # avant de valider le test!
    excel_van_projet_attendu = 6765.0   # REMPLACER AVEC LA VALEUR RÉELLE DE VOTRE EXCEL
    excel_tri_projet_attendu = 0.1056   # REMPLACER AVEC LA VALEUR RÉELLE DE VOTRE EXCEL (10.56%)
    excel_lcoe_attendu = 0.1362         # REMPLACER AVEC LA VALEUR RÉELLE DE VOTRE EXCEL
    excel_payback_projet_attendu = 2.8  # REMPLACER AVEC LA VALEUR RÉELLE DE VOTRE EXCEL
    
    # Indicateurs annuels (Exemple pour la 1ère année complète - Année 1 de l'exploitation)
    # IMPORTANT: Remplacer ces valeurs par celles de votre Excel Golden Sample
    excel_an1_revenus_total = 8250.0  # REMPLACER (55000 kWh * 0.15 €/kWh)
    excel_an1_ebitda = 6950.0         # REMPLACER (8250 - 1000 (OPEX) - 300 (TURPE))
    excel_an1_ebt = -3050.0           # REMPLACER (6950 - 10000 (Amort))
    excel_an1_is = 0.0                # REMPLACER (EBT < 0 ou tranche PME à 15%)
    excel_an1_resultat_net = -3050.0  # REMPLACER
    excel_an1_fcfe = 6950.0           # REMPLACER (-3050 (RN) + 10000 (Amort))
    excel_an1_ocf_projet = 6950.0     # REMPLACER

    print(f"\n  --- Comparaison Indicateurs Globaux ---")
    print(f"  VAN Projet: Moteur={engine_van_projet:,.2f} €, Excel Attendu={excel_van_projet_attendu:,.2f} €")
    print(f"  TRI Projet: Moteur={engine_tri_projet*100:.4f}%, Excel Attendu={excel_tri_projet_attendu*100:.4f}%")
    print(f"  LCOE: Moteur={engine_lcoe:.6f}, Excel Attendu={excel_lcoe_attendu:.6f}")
    print(f"  Payback Projet: Moteur={engine_payback_projet:.2f} ans, Excel Attendu={excel_payback_projet_attendu:.2f} ans")
    
    # Calcul des écarts en pourcentage
    if excel_van_projet_attendu != 0:
        ecart_van_pct = abs((engine_van_projet - excel_van_projet_attendu) / excel_van_projet_attendu * 100)
        print(f"  Écart VAN: {ecart_van_pct:.2f}%")
    
    if excel_tri_projet_attendu != 0:
        ecart_tri_pct = abs((engine_tri_projet - excel_tri_projet_attendu) / excel_tri_projet_attendu * 100)
        print(f"  Écart TRI: {ecart_tri_pct:.2f}%")
    
    if excel_lcoe_attendu != 0:
        ecart_lcoe_pct = abs((engine_lcoe - excel_lcoe_attendu) / excel_lcoe_attendu * 100)
        print(f"  Écart LCOE: {ecart_lcoe_pct:.2f}%")

    # Assertions (avec une tolérance pour les flottants)
    # NOTE: Augmenter la tolérance si nécessaire pendant la phase d'alignement
    assert math.isclose(engine_van_projet, excel_van_projet_attendu, rel_tol=0.01, abs_tol=5.0), \
        f"VAN Projet: Moteur={engine_van_projet:.2f}€ vs Excel={excel_van_projet_attendu:.2f}€"
    
    assert math.isclose(engine_tri_projet, excel_tri_projet_attendu, rel_tol=0.01, abs_tol=0.001), \
        f"TRI Projet: Moteur={engine_tri_projet*100:.4f}% vs Excel={excel_tri_projet_attendu*100:.4f}%"
    
    assert math.isclose(engine_lcoe, excel_lcoe_attendu, rel_tol=0.01, abs_tol=0.001), \
        f"LCOE: Moteur={engine_lcoe:.6f} vs Excel={excel_lcoe_attendu:.6f}"
    
    if pd.notna(engine_payback_projet) and pd.notna(excel_payback_projet_attendu):
         assert math.isclose(engine_payback_projet, excel_payback_projet_attendu, rel_tol=0.01, abs_tol=0.1), \
             f"Payback: Moteur={engine_payback_projet:.2f} ans vs Excel={excel_payback_projet_attendu:.2f} ans"

    # --- Comparaison des Agrégats Annuels (Année 1 d'exploitation) ---
    annee_1_exploitation = pd.to_datetime(cfg["date_debut_ppa"]).year
    df_an1_engine = df_monthly_engine[df_monthly_engine.index.year == annee_1_exploitation]

    if not df_an1_engine.empty:
        engine_an1_revenus = df_an1_engine['Revenus_Total'].sum()
        engine_an1_ebitda = df_an1_engine['EBITDA'].sum()
        engine_an1_ebt = df_an1_engine['EBT'].sum()
        engine_an1_is_paye = df_an1_engine['Total_IS_Decaisse_Mois'].sum()
        engine_an1_resultat_net = df_an1_engine['Resultat_Net'].sum()
        engine_an1_fcfe = df_an1_engine['FCFE'].sum()
        engine_an1_ocf_projet = df_an1_engine['OCF_Projet'].sum()

        print(f"\n  --- Comparaison Agrégats Année 1 ({annee_1_exploitation}) ---")
        print(f"  Revenus: Moteur={engine_an1_revenus:,.2f}, Excel={excel_an1_revenus_total:,.2f}, Écart={abs((engine_an1_revenus-excel_an1_revenus_total)/excel_an1_revenus_total*100):.2f}%")
        print(f"  EBITDA:  Moteur={engine_an1_ebitda:,.2f}, Excel={excel_an1_ebitda:,.2f}, Écart={abs((engine_an1_ebitda-excel_an1_ebitda)/excel_an1_ebitda*100):.2f}%")
        print(f"  EBT: Moteur={engine_an1_ebt:,.2f}, Excel={excel_an1_ebt:,.2f}")
        print(f"  IS Payé: Moteur={engine_an1_is_paye:,.2f}, Excel={excel_an1_is:,.2f}")
        print(f"  Résultat Net: Moteur={engine_an1_resultat_net:,.2f}, Excel={excel_an1_resultat_net:,.2f}")
        print(f"  FCFE: Moteur={engine_an1_fcfe:,.2f}, Excel={excel_an1_fcfe:,.2f}, Écart={abs((engine_an1_fcfe-excel_an1_fcfe)/excel_an1_fcfe*100) if excel_an1_fcfe != 0 else 'N/A'}%")
        print(f"  OCF Projet: Moteur={engine_an1_ocf_projet:,.2f}, Excel={excel_an1_ocf_projet:,.2f}, Écart={abs((engine_an1_ocf_projet-excel_an1_ocf_projet)/excel_an1_ocf_projet*100) if excel_an1_ocf_projet != 0 else 'N/A'}%")

        # Assertions pour les agrégats annuels
        # NOTE: Ajuster les tolérances selon vos besoins pendant la phase d'alignement
        assert math.isclose(engine_an1_revenus, excel_an1_revenus_total, rel_tol=0.01), \
            f"Revenus An1: Moteur={engine_an1_revenus:.2f}€ vs Excel={excel_an1_revenus_total:.2f}€"
        
        assert math.isclose(engine_an1_ebitda, excel_an1_ebitda, rel_tol=0.01), \
            f"EBITDA An1: Moteur={engine_an1_ebitda:.2f}€ vs Excel={excel_an1_ebitda:.2f}€"
        
        # Pour EBT, IS et RN, la comparaison peut être plus complexe à cause des différences
        # dans le calcul mensuel vs annuel de l'IS. Utiliser une tolérance plus élevée.
        assert math.isclose(engine_an1_fcfe, excel_an1_fcfe, rel_tol=0.02), \
            f"FCFE An1: Moteur={engine_an1_fcfe:.2f}€ vs Excel={excel_an1_fcfe:.2f}€"
        
        assert math.isclose(engine_an1_ocf_projet, excel_an1_ocf_projet, rel_tol=0.02), \
            f"OCF Projet An1: Moteur={engine_an1_ocf_projet:.2f}€ vs Excel={excel_an1_ocf_projet:.2f}€"
    else:
        print(f"AVERTISSEMENT: Aucune donnée pour l'année {annee_1_exploitation} dans les résultats du moteur.")
        
    print("\n--- Test Golden Sample Terminé ---")
    print("IMPORTANT: Pour valider ce test, vous devez mettre à jour les valeurs 'excel_xxx_attendu'")
    print("avec les valeurs réelles de votre modèle Excel après alignement complet des hypothèses.")