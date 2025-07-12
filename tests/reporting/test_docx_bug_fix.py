"""
Test pour vérifier la correction du bug DOCX
Vérifie que le message d'avertissement n'apparaît pas quand il ne devrait pas
"""

import streamlit as st
import sys
import os
from unittest.mock import Mock, patch

# Ajouter le chemin parent au système
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from modules.reporting.docx_integration import DocxIntegrationModule

def test_docx_status_without_warnings():
    """Test que get_system_status n'affiche pas de warnings"""
    
    # Initialiser session state
    st.session_state.clear()
    
    # Créer une instance du module
    docx_module = DocxIntegrationModule()
    
    # Test 1: Sans données importées
    st.session_state['data_imported'] = False
    
    # Capturer les warnings
    with patch.object(st, 'warning') as mock_warning:
        status = docx_module.get_system_status()
        
        # Vérifier qu'aucun warning n'a été affiché
        assert mock_warning.call_count == 0, f"Des warnings ont été affichés: {mock_warning.call_args_list}"
        
        # Vérifier que prerequisites_ok est False
        assert status['prerequisites_ok'] == False
    
    print("✅ Test 1 réussi: Pas de warning lors du check de status sans données")
    
    # Test 2: Avec données mais sans optimisation
    st.session_state['data_imported'] = True
    st.session_state['optimization_results'] = None
    
    with patch.object(st, 'warning') as mock_warning:
        status = docx_module.get_system_status()
        
        # Vérifier qu'aucun warning n'a été affiché
        assert mock_warning.call_count == 0, f"Des warnings ont été affichés: {mock_warning.call_args_list}"
        
        # Vérifier que prerequisites_ok est False
        assert status['prerequisites_ok'] == False
    
    print("✅ Test 2 réussi: Pas de warning lors du check de status sans optimisation")
    
    # Test 3: Avec données et optimisation
    st.session_state['data_imported'] = True
    st.session_state['optimization_results'] = {'some': 'results'}
    
    with patch.object(st, 'warning') as mock_warning:
        status = docx_module.get_system_status()
        
        # Vérifier qu'aucun warning n'a été affiché
        assert mock_warning.call_count == 0
        
        # Vérifier que prerequisites_ok est True (si le système est disponible)
        if status['available']:
            assert status['prerequisites_ok'] == True
    
    print("✅ Test 3 réussi: Pas de warning lors du check de status avec toutes les données")

def test_check_prerequisites_with_warnings():
    """Test que _check_prerequisites affiche des warnings quand demandé"""
    
    # Initialiser session state
    st.session_state.clear()
    st.session_state['data_imported'] = False
    
    # Créer une instance du module
    docx_module = DocxIntegrationModule()
    
    # Test avec show_warnings=True (par défaut)
    with patch.object(st, 'warning') as mock_warning:
        result = docx_module._check_prerequisites()
        
        # Vérifier qu'un warning a été affiché
        assert mock_warning.call_count == 1
        assert "Aucune donnée n'a été importée" in str(mock_warning.call_args)
    
    print("✅ Test 4 réussi: Warning affiché quand show_warnings=True")
    
    # Test avec show_warnings=False
    with patch.object(st, 'warning') as mock_warning:
        result = docx_module._check_prerequisites(show_warnings=False)
        
        # Vérifier qu'aucun warning n'a été affiché
        assert mock_warning.call_count == 0
    
    print("✅ Test 5 réussi: Pas de warning quand show_warnings=False")

if __name__ == "__main__":
    print("🧪 Début des tests du bug fix DOCX...")
    
    try:
        test_docx_status_without_warnings()
        test_check_prerequisites_with_warnings()
        
        print("\n✅ Tous les tests sont passés avec succès!")
        print("\n📝 Résumé du fix:")
        print("- La méthode _check_prerequisites accepte maintenant un paramètre show_warnings")
        print("- get_system_status appelle _check_prerequisites avec show_warnings=False")
        print("- Cela empêche l'affichage de warnings lors du simple check de status")
        print("- Le bloc else impossible dans customer_report_commercial.py a été supprimé")
        
    except AssertionError as e:
        print(f"\n❌ Échec du test: {e}")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()