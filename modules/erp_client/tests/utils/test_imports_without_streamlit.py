"""Test des imports en mockant Streamlit pour éviter la dépendance.

Ce test remplace temporairement streamlit par un mock pour tester
tous les autres imports et détecter les vraies erreurs.
"""

import sys
import types
import importlib
from pathlib import Path
from unittest.mock import MagicMock

def create_streamlit_mock():
    """Crée un mock complet de Streamlit."""
    mock_st = MagicMock()
    
    # Mock des fonctions principales de Streamlit
    mock_st.title = MagicMock()
    mock_st.header = MagicMock()
    mock_st.subheader = MagicMock()
    mock_st.write = MagicMock()
    mock_st.markdown = MagicMock()
    mock_st.text = MagicMock()
    mock_st.caption = MagicMock()
    mock_st.code = MagicMock()
    mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
    mock_st.container = MagicMock()
    mock_st.tabs = MagicMock(return_value=[MagicMock() for _ in range(10)])
    mock_st.expander = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.button = MagicMock(return_value=False)
    mock_st.selectbox = MagicMock(return_value="default")
    mock_st.multiselect = MagicMock(return_value=[])
    mock_st.text_input = MagicMock(return_value="")
    mock_st.number_input = MagicMock(return_value=0)
    mock_st.checkbox = MagicMock(return_value=False)
    mock_st.radio = MagicMock(return_value="default")
    mock_st.slider = MagicMock(return_value=0)
    mock_st.file_uploader = MagicMock(return_value=None)
    mock_st.download_button = MagicMock()
    mock_st.metric = MagicMock()
    mock_st.progress = MagicMock()
    mock_st.balloons = MagicMock()
    mock_st.success = MagicMock()
    mock_st.info = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.error = MagicMock()
    mock_st.exception = MagicMock()
    mock_st.help = MagicMock()
    mock_st.rerun = MagicMock()
    mock_st.empty = MagicMock()
    mock_st.plotly_chart = MagicMock()
    mock_st.dataframe = MagicMock()
    mock_st.data_editor = MagicMock()
    mock_st.table = MagicMock()
    mock_st.json = MagicMock()
    mock_st.image = MagicMock()
    mock_st.audio = MagicMock()
    mock_st.video = MagicMock()
    mock_st.map = MagicMock()
    mock_st.popover = MagicMock()
    mock_st.divider = MagicMock()
    
    # Mock session_state avec support d'attributs
    class MockSessionState(dict):
        def __getattr__(self, name):
            return self.get(name)
        def __setattr__(self, name, value):
            self[name] = value
    
    mock_st.session_state = MockSessionState()
    
    # Mock configuration
    mock_st.set_page_config = MagicMock()
    
    # Mock column_config
    mock_column_config = MagicMock()
    mock_column_config.CheckboxColumn = MagicMock()
    mock_column_config.NumberColumn = MagicMock()
    mock_column_config.TextColumn = MagicMock()
    mock_column_config.SelectboxColumn = MagicMock()
    mock_column_config.ProgressColumn = MagicMock()
    mock_column_config.DateColumn = MagicMock()
    mock_column_config.LinkColumn = MagicMock()
    mock_st.column_config = mock_column_config
    
    return mock_st

def mock_other_dependencies():
    """Mock d'autres dépendances potentiellement manquantes."""
    
    # Mock numpy si pas installé
    if 'numpy' not in sys.modules:
        mock_numpy = MagicMock()
        mock_numpy.array = MagicMock()
        mock_numpy.zeros = MagicMock()
        mock_numpy.ones = MagicMock()
        mock_numpy.polyfit = MagicMock()
        sys.modules['numpy'] = mock_numpy
    
    # Mock plotly si pas installé
    if 'plotly' not in sys.modules:
        mock_plotly = MagicMock()
        mock_plotly.graph_objects = MagicMock()
        mock_plotly.express = MagicMock()
        mock_plotly.subplots = MagicMock()
        mock_plotly.subplots.make_subplots = MagicMock()
        sys.modules['plotly'] = mock_plotly
        sys.modules['plotly.graph_objects'] = mock_plotly.graph_objects
        sys.modules['plotly.express'] = mock_plotly.express
        sys.modules['plotly.subplots'] = mock_plotly.subplots
    
    # Mock pandas si pas installé
    if 'pandas' not in sys.modules:
        mock_pandas = MagicMock()
        mock_pandas.DataFrame = MagicMock()
        mock_pandas.Series = MagicMock()
        mock_pandas.date_range = MagicMock()
        sys.modules['pandas'] = mock_pandas
    
    # Mock folium si pas installé
    if 'folium' not in sys.modules:
        mock_folium = MagicMock()
        mock_folium.plugins = MagicMock()
        mock_folium.Map = MagicMock()
        mock_folium.Marker = MagicMock()
        mock_folium.Circle = MagicMock()
        sys.modules['folium'] = mock_folium
        sys.modules['folium.plugins'] = mock_folium.plugins
    
    # Mock scipy si pas installé
    if 'scipy' not in sys.modules:
        mock_scipy = MagicMock()
        mock_scipy.optimize = MagicMock()
        mock_scipy.optimize.minimize = MagicMock()
        mock_scipy.optimize.brentq = MagicMock()
        sys.modules['scipy'] = mock_scipy
        sys.modules['scipy.optimize'] = mock_scipy.optimize
    
    # Mock openpyxl si pas installé
    if 'openpyxl' not in sys.modules:
        mock_openpyxl = MagicMock()
        sys.modules['openpyxl'] = mock_openpyxl

def test_app_imports():
    """Teste les imports de app.py avec mocks."""
    print("🔍 Test imports app.py avec mocks...")
    
    # Ajouter le projet au path
    project_root = Path(__file__).parent.parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Installer les mocks
    mock_st = create_streamlit_mock()
    sys.modules['streamlit'] = mock_st
    mock_other_dependencies()
    
    try:
        # Importer app.py
        import app
        print("✅ Import app.py réussi!")
        
        # Tester quelques fonctions si elles existent
        if hasattr(app, 'main'):
            print("✅ Fonction main() trouvée")
        
        return True, []
        
    except Exception as e:
        print(f"❌ Erreur import app.py: {e}")
        import traceback
        error_details = traceback.format_exc()
        print(f"Détails: {error_details}")
        return False, [str(e)]

def test_erp_module_imports():
    """Teste les imports du module ERP avec mocks."""
    print("🔍 Test imports module ERP...")
    
    errors = []
    
    try:
        # Test import des modèles directement
        from modules.erp_client.models.client import Client, TypeClient
        print("✅ Import models.client OK")
        
        from modules.erp_client.models.pricing import PrixClient, TypeTarif
        print("✅ Import models.pricing OK")
        
        # Test TypeClient enum
        assert TypeClient.PRODUCTEUR.value == "producteur"
        print("✅ TypeClient enum fonctionne")
        
        # Test création d'un client
        client = Client(
            code_client="TEST001",
            nom="Test Client",
            type_client=TypeClient.PRODUCTEUR
        )
        print("✅ Création Client réussie")
        
        return True, errors
        
    except Exception as e:
        error_msg = f"Erreur ERP imports: {e}"
        print(f"❌ {error_msg}")
        errors.append(error_msg)
        return False, errors

def test_services_imports():
    """Teste les imports des services ERP."""
    print("🔍 Test imports services ERP...")
    
    errors = []
    services_to_test = [
        "modules.erp_client.services.client_service",
        "modules.erp_client.services.pricing_service", 
        "modules.erp_client.services.capacity_service"
    ]
    
    for service_module in services_to_test:
        try:
            importlib.import_module(service_module)
            print(f"✅ Import {service_module} OK")
        except Exception as e:
            error_msg = f"Erreur import {service_module}: {e}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
    
    return len(errors) == 0, errors

def test_ui_imports():
    """Teste les imports des modules UI."""
    print("🔍 Test imports UI modules...")
    
    errors = []
    ui_modules = [
        "modules.erp_client.ui.client_form",
        "modules.erp_client.ui.client_list",
        "modules.erp_client.ui.pricing_dashboard"
    ]
    
    for ui_module in ui_modules:
        try:
            importlib.import_module(ui_module)
            print(f"✅ Import {ui_module} OK")
        except Exception as e:
            error_msg = f"Erreur import {ui_module}: {e}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
    
    return len(errors) == 0, errors

def main():
    """Fonction principale de test."""
    print("🧪 TEST COMPLET DES IMPORTS (AVEC MOCKS)")
    print("="*60)
    print("Ce test mock Streamlit et autres dépendances pour tester les imports")
    print("="*60)
    
    all_errors = []
    test_results = []
    
    # Test 1: App principal
    app_ok, app_errors = test_app_imports()
    test_results.append(("App principal", app_ok))
    all_errors.extend(app_errors)
    
    # Test 2: Module ERP
    erp_ok, erp_errors = test_erp_module_imports()
    test_results.append(("Module ERP", erp_ok))
    all_errors.extend(erp_errors)
    
    # Test 3: Services
    services_ok, services_errors = test_services_imports()
    test_results.append(("Services ERP", services_ok))
    all_errors.extend(services_errors)
    
    # Test 4: UI modules
    ui_ok, ui_errors = test_ui_imports()
    test_results.append(("Modules UI", ui_ok))
    all_errors.extend(ui_errors)
    
    # Résumé final
    print("\n" + "="*60)
    print("📊 RÉSUMÉ FINAL")
    print("="*60)
    
    passed = sum(1 for _, ok in test_results if ok)
    total = len(test_results)
    
    for test_name, ok in test_results:
        status = "✅ PASSÉ" if ok else "❌ ÉCHEC"
        print(f"{status}: {test_name}")
    
    print(f"\nRésultat: {passed}/{total} tests passés")
    print(f"Erreurs totales: {len(all_errors)}")
    
    if len(all_errors) == 0:
        print("\n🎉 AUCUNE ERREUR D'IMPORT DÉTECTÉE!")
        print("✅ Tous les modules peuvent être importés (sans Streamlit)")
    else:
        print(f"\n⚠️ {len(all_errors)} erreur(s) détectée(s):")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
    
    return len(all_errors) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)