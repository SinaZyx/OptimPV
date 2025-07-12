# tests/test_analysis_engine.py
import math
import numpy as np
import pandas as pd
import pytest
import sys
import os
import json
import copy
from datetime import datetime

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

# --- NOUVEAU TEST : Production Nulle une Année ---
def test_zero_production_year_impact(
    base_config_real, scenarios_real, sites_config_real, single_site_real_data_fixture
):
    """Teste l'impact d'une année sans production sur LCOE et autres indicateurs."""
    cfg = base_config_real.copy()
    
    # Préparer les données de site avec une année de production nulle
    site_data_modified = single_site_real_data_fixture.copy() # Correct: single_site_real_data_fixture IS a dict here
    site_key = list(site_data_modified.keys())[0] # Récupérer la clé du site
    df_site = site_data_modified[site_key].copy()

    # S'assurer que l'index Temps est de type datetime
    if not pd.api.types.is_datetime64_any_dtype(df_site['Temps']):
        # Tentative de conversion avec un format PVSOL courant et un fallback
        def convert_time_format_robust(time_val):
            if isinstance(time_val, (datetime, pd.Timestamp)): return time_val
            try: # Format "DD.MM. HH:MM"
                parts = str(time_val).split(' '); date_part = parts[0]; time_part = parts[1]
                day, month = map(int, date_part.split('.')[0:2]); hour, minute = map(int, time_part.split(':'))
                # Utiliser l'année de début PPA de la config pour construire la date
                # si l'année n'est pas dans la chaîne de temps.
                # Pour ce test, on peut supposer une année fixe si non présente.
                # La logique de data_processing.py est plus robuste pour cela.
                # Ici, on va essayer de la rendre cohérente avec date_debut_ppa.
                year_for_conversion = pd.to_datetime(cfg.get("date_debut_ppa", "2025-01-01")).year

                # Détecter si l'année est manquante (ex: "DD.MM. HH:MM")
                # Si date_part ressemble à "DD.MM." ou "DD.MM", alors l'année est manquante
                if len(date_part.split('.')) == 2 or (len(date_part.split('.')) == 3 and not date_part.split('.')[2]):
                     return datetime(year_for_conversion, month, day, hour, minute)
                else: # L'année devrait être présente (DD.MM.YY ou DD.MM.YYYY)
                     return pd.to_datetime(str(time_val).replace('.', '/'), dayfirst=True, errors='coerce') # Tenter avec dayfirst

            except Exception: # Fallback général
                 return pd.to_datetime(time_val, errors='coerce')
        df_site['Temps'] = df_site['Temps'].apply(convert_time_format_robust)
        df_site = df_site.dropna(subset=['Temps'])
        if df_site.empty: pytest.skip("Échec conversion temps pour test_zero_production_year_impact")
    
    df_site = df_site.set_index('Temps') # Mettre 'Temps' en index pour resample
 
    # Forcer la production à zéro pour la deuxième année d'exploitation (par exemple 2026)
    # La première année d'exploitation est 2025 car duree_construction = 0 dans base_config_real (par défaut)
    # Mais date_debut_ppa peut être différent, donc on se base sur ça.
    date_debut_ppa_dt = pd.to_datetime(cfg.get("date_debut_ppa", "2025-01-01"))
    year_with_zero_production = date_debut_ppa_dt.year + 1
    
    if not df_site.empty and year_with_zero_production in df_site.index.year:
        df_site.loc[df_site.index.year == year_with_zero_production, 'production_kwh'] = 0.0
        print(f"INFO: Production pour l'année {year_with_zero_production} mise à zéro pour le test.")
    else:
        print(f"AVERTISSEMENT: L'année {year_with_zero_production} n'est pas dans les données ({df_site.index.year.min()}-{df_site.index.year.max()}) ou données vides, test de production nulle pourrait ne pas être pertinent.")
        # Si l'année n'est pas présente, le test n'est pas très significatif.
        # On pourrait skipper le test ou s'attendre à ce que le LCOE soit NaN si la production globale devient nulle.
 
    site_data_modified[site_key] = df_site.reset_index() # Remettre Temps en colonne pour AnalysisEngine
 
    engine = AnalysisEngine(cfg, scenarios_real, site_data_modified) # Utilise les données modifiées
    results = engine.calculate_financial_indicators(
        "Base", 
        prix_revente=cfg.get("prix_vente_initial_slider_fallback", 0.10), 
        sites_config=sites_config_real # sites_config_real est utilisé pour les paramètres du site (OPEX, etc.), mais site_data_modified pour les données horaires
    )
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}"
    
    lcoe = results.get("lcoe")
    npv_project = results.get("npv_project")
    irr_project = results.get("irr_project")
 
    print(f"\n--- Test Production Nulle Année {year_with_zero_production} ---")
    print(f"  LCOE: {lcoe:.4f} €/kWh" if lcoe is not None else "N/A")
    print(f"  VAN Projet: {npv_project:,.0f} €" if npv_project is not None else "N/A")
    print(f"  TRI Projet: {irr_project*100:.2f}%" if irr_project is not None else "N/A")
 
    # Attentes : Le LCOE devrait augmenter (car même coûts pour moins de production actualisée).
    # La VAN et le TRI Projet devraient chuter.
    # Si la production totale devient trop faible, LCOE pourrait être NaN (ce que la fonction gère).
    
    # Pour une assertion plus forte, il faudrait comparer avec un cas de base où la production n'est pas nulle.
    # On peut stocker le LCOE/VAN/TRI du cas de base (premier cas de test_project_irr_with_debt_levels par exemple)
    # ou le recalculer ici sans la modification de production.
    
    # Recalculons le cas de base SANS production nulle pour comparer
    engine_base_case = AnalysisEngine(cfg, scenarios_real, single_site_real_data_fixture) # Données originales
    results_base_case = engine_base_case.calculate_financial_indicators(
        "Base", 
        prix_revente=cfg.get("prix_vente_initial_slider_fallback", 0.10), 
        sites_config=sites_config_real
    )
    assert results_base_case and "error" not in results_base_case
    
    lcoe_base = results_base_case.get("lcoe")
    npv_project_base = results_base_case.get("npv_project")
    irr_project_base = results_base_case.get("irr_project")
 
    print(f"  Référence (sans prod. nulle): LCOE={'N/A' if pd.isna(lcoe_base) else f'{lcoe_base:.4f}'}, "
          f"VAN={'N/A' if pd.isna(npv_project_base) else f'{npv_project_base:,.0f}'}, "
          f"TRI={'N/A' if pd.isna(irr_project_base) else f'{(irr_project_base*100):.2f}%'}")
 
    if lcoe is not None and lcoe_base is not None:
        assert lcoe > lcoe_base - 1e-4, "LCOE avec une année de production nulle devrait être plus élevé."
    # Si la production est nulle une année, la VAN et le TRI devraient être significativement plus bas, ou le TRI pourrait même devenir non calculable/négatif.
    if npv_project is not None and npv_project_base is not None:
        assert npv_project < npv_project_base + 1, "VAN Projet avec une année de production nulle devrait être plus basse."
    if irr_project is not None and irr_project_base is not None:
        # L'IRR peut devenir non significatif ou très différent.
        # Une simple comparaison < peut être suffisante si le projet de base est rentable.
        # Si le projet de base a un TRI très bas, la comparaison est plus délicate.
        # Pour l'instant, on s'attend à une baisse.
        assert irr_project < irr_project_base + 1e-4, "TRI Projet avec une année de production nulle devrait être plus bas."
        
# S'assurer que les autres tests existants sont toujours là
# test_calculate_wacc_numeric, test_project_irr_with_debt_levels, test_van_project_with_zero_wacc,
# test_financial_statements_coherence_for_bank, test_inflation_impact, test_terminal_value_impact,
# test_wacc_rd_greater_than_re

# --- Fixtures Additionnelles ou Modifiées pour Nouveaux Tests ---

@pytest.fixture(scope="function")
def data_for_temporal_test():
    """Crée des données horaires pour un projet avec construction et exploitation décalées."""
    # Construction: Oct N   -> Déc N+1 (15 mois)
    # Exploitation: Jan N+2 -> Mar N+20 (18 ans + 3 mois)
    
    # Dates de début pour la fixture (peuvent être ajustées par la config du test)
    # Pour que les tests soient reproductibles, utilisons des dates fixes ici.
    # date_debut_construction_fixture = pd.Timestamp("2025-10-01")
    # date_debut_exploitation_fixture = pd.Timestamp("2027-01-01")
    # Pour que l'engine utilise ces dates, elles doivent être dans la config.
    # La fixture de données horaires doit couvrir toute la période.

    # Durée totale de simulation : 15 mois construction + (18*12 + 3) mois exploitation = 15 + 216 + 3 = 234 mois
    # Si la config passée au test définit date_debut_ppa et duree_construction,
    # l'engine calculera lui-même date_debut_simulation_effective.
    # La fixture de données doit juste fournir assez de données horaires brutes.
    
    # Générons des données horaires pour environ 20 ans pour couvrir les besoins
    # L'engine se basera sur date_debut_ppa et duree_construction de la config.
    start_date_data = pd.Timestamp("2025-01-01") # Assez tôt pour couvrir
    total_periods_data = 20 * 365 * 24 # Approx 20 ans de données horaires
    
    hourly_index = pd.date_range(start=start_date_data, periods=total_periods_data, freq='h')
    df = pd.DataFrame(index=hourly_index)
    df['Temps'] = df.index.strftime('%Y-%m-%d %H:%M:%S') # Format que l'engine peut parser
    
    # Profil simple : production constante pendant 8h/jour, conso constante sur 24h
    # Ces valeurs sont des moyennes et seront répétées.
    # La fixture `daily_profile` est plus élaborée, mais pour un test de temporalité,
    # la présence de données sur la bonne période est plus importante que le profil exact.
    df['production_kwh_raw'] = np.where((df.index.hour >= 8) & (df.index.hour < 16), 10.0, 0.0) # 10 kWh/h pendant 8h
    df['consumption_kwh_raw'] = 5.0 # 5 kWh/h constant
    
    # Renommer pour correspondre à ce que `load_and_prepare_single_site_excel_data_for_test` produirait
    # ou ce que `validate_and_prepare_sites_data` attend.
    df = df.rename(columns={'production_kwh_raw': 'production_kwh', 'consumption_kwh_raw': 'consumption_kwh'})
    
    return {"site_temporal_test": df[['Temps', 'production_kwh', 'consumption_kwh']]}


# -----------------------------------------------------------------------------
# NOUVEAUX TESTS ADDITIONNELS
# -----------------------------------------------------------------------------

# --- Couverture Fonctionnelle Manquante ---

def test_temporality_construction_exploitation_offset(
    base_config_real, scenarios_real, sites_config_real, data_for_temporal_test
):
    """
    Teste un scénario avec construction et exploitation décalées.
    Construction: Oct N -> Déc N+1 (15 mois)
    Exploitation: Jan N+2 -> ...
    Vérifie que les indicateurs clés (VAN, TRI) sont calculés et cohérents.
    """
    cfg = base_config_real.copy()
    cfg.update({
        "date_debut_ppa": "2027-01-01", # Début exploitation Jan N+2 (si N=2025)
        "duree_construction": 15,       # 15 mois
        "duree_ppa": (18 * 12) + 3,     # 18 ans et 3 mois d'exploitation
        # Garder les autres paramètres financiers (CAPEX, OPEX, taux) de base_config_real
        # pour que le projet soit potentiellement rentable.
        "capex_scenario": 65000, # Assurer un CAPEX
        "puissance_kwc_installee": 45,
    })

    # Utiliser la config de site par défaut pour ce test,
    # mais s'assurer que le site_key correspond à celui dans data_for_temporal_test
    site_key_temporal = list(data_for_temporal_test.keys())[0]
    current_sites_config = {site_key_temporal: sites_config_real.get(list(sites_config_real.keys())[0], {})} 
    # Ou si sites_config_real est déjà structuré par nom de fichier et que data_for_temporal_test utilise
    # une clé qui s'y trouve, on peut utiliser sites_config_real directement.
    # Pour ce test, forçons une config de site simple si besoin:
    if not current_sites_config.get(site_key_temporal) or not current_sites_config[site_key_temporal]:
        current_sites_config[site_key_temporal] = {
            'capex': cfg["capex_scenario"], # S'assurer que le CAPEX est pris
            'puissance_kwc': cfg["puissance_kwc_installee"],
            'opex_maintenance': cfg.get("opex_maintenance_fallback", 200),
            'opex_insurance': cfg.get("opex_insurance_fallback", 100),
            'opex_admin': cfg.get("opex_admin_fallback", 100),
            'opex_onduleur_provision_site': False
        }


    engine = AnalysisEngine(cfg, scenarios_real, data_for_temporal_test)
    results = engine.calculate_financial_indicators(
        "Base",
        prix_revente=cfg.get("prix_vente_initial_slider_fallback", 0.12), # Un prix potentiellement rentable
        sites_config=current_sites_config
    )
    assert results and "error" not in results, f"Erreur Engine: {results.get('error')}"

    npv_project = results.get("npv_project")
    irr_project = results.get("irr_project")
    lcoe = results.get("lcoe")
    df_monthly = results.get("monthly_data")

    print(f"\n--- Test Temporalité Décalée ---")
    print(f"  Date début PPA (exploitation): {cfg['date_debut_ppa']}")
    print(f"  Durée construction: {cfg['duree_construction']} mois")
    print(f"  VAN Projet: {npv_project:,.0f} €" if npv_project is not None else "N/A")
    print(f"  TRI Projet: {irr_project*100:.2f}%" if irr_project is not None else "N/A")
    print(f"  LCOE: {lcoe:.4f} €/kWh" if lcoe is not None else "N/A")

    assert pd.notna(npv_project), "VAN Projet ne devrait pas être NaN"
    assert pd.notna(irr_project), "TRI Projet ne devrait pas être NaN"
    assert pd.notna(lcoe), "LCOE ne devrait pas être NaN"

    # Vérifier le nombre de mois de construction et d'exploitation dans les résultats
    num_construction_months_results = df_monthly['Is_Construction_Phase'].sum()
    num_exploitation_months_results = len(df_monthly) - num_construction_months_results

    assert math.isclose(num_construction_months_results, cfg['duree_construction']), \
        f"Nombre de mois de construction dans les résultats ({num_construction_months_results}) " \
        f"ne correspond pas à la config ({cfg['duree_construction']})."
    
    assert math.isclose(num_exploitation_months_results, cfg['duree_ppa']), \
        f"Nombre de mois d'exploitation dans les résultats ({num_exploitation_months_results}) " \
        f"ne correspond pas à la config ({cfg['duree_ppa']})."
        
    # Vérifier que la première date d'exploitation est correcte
    first_op_date_results = df_monthly[df_monthly['Is_Construction_Phase'] == 0.0].index.min()
    expected_first_op_date = pd.to_datetime(cfg['date_debut_ppa'])
    # L'index de df_monthly est en fin de mois (ME).
    # date_debut_ppa est un jour. Il faut comparer l'année et le mois.
    assert first_op_date_results.year == expected_first_op_date.year and \
           first_op_date_results.month == expected_first_op_date.month, \
           f"Première date d'exploitation ({first_op_date_results}) ne correspond pas à la date de début PPA configurée ({expected_first_op_date})."


# --- Tests d'Edge Cases ---

def test_lcoe_with_total_zero_production(
    base_config_real, scenarios_real, sites_config_real, single_site_real_data_fixture
):
    """Teste le calcul du LCOE quand la production totale sur la durée est nulle."""
    cfg = base_config_real.copy()
    
    # Modifier les données pour avoir une production nulle sur toute la durée
    site_data_zero_prod = single_site_real_data_fixture.copy()
    site_key = list(site_data_zero_prod.keys())[0]
    df_site = site_data_zero_prod[site_key].copy()
    df_site['production_kwh'] = 0.0 # Forcer toute la production à zéro
    site_data_zero_prod[site_key] = df_site

    engine = AnalysisEngine(cfg, scenarios_real, site_data_zero_prod)
    results = engine.calculate_financial_indicators(
        "Base",
        prix_revente=0.10, # Prix non critique ici
        sites_config=sites_config_real
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

# --- FIN DES NOUVEAUX TESTS ---

# S'assurer que les autres tests existants sont toujours là et corrects
# test_calculate_wacc_numeric, test_project_irr_with_debt_levels, test_van_project_with_zero_wacc,
# test_financial_statements_coherence_for_bank, test_inflation_impact, test_terminal_value_impact,
# test_wacc_rd_greater_than_re, test_zero_production_year_impact, etc.