"""Hook d'intégration pour le module core_analyzer.

Ce fichier doit être importé dans core_analyzer.py pour activer
la sélection de clients depuis l'ERP.
"""

import streamlit as st
from typing import Optional, Dict, Any

def inject_client_selector():
    """Injecte le sélecteur de client dans l'interface du core_analyzer.
    
    Cette fonction doit être appelée au début de l'analyse pour permettre
    la sélection d'un client avec ses tarifs personnalisés.
    """
    try:
        from ..integration.analysis_connector import AnalysisConnector
        
        # Créer le connecteur
        connector = AnalysisConnector()
        
        # Afficher le sélecteur si pas de client sélectionné
        if not st.session_state.get('current_client'):
            st.info("💡 Vous pouvez maintenant sélectionner un client depuis la base ERP pour appliquer ses tarifs personnalisés.")
            
            # Widget de sélection
            selected_client = connector.render_client_selector_widget()
            
            if selected_client:
                st.success(f"✅ Client '{selected_client.nom}' sélectionné avec ses tarifs")
                return True
            else:
                st.warning("⚠️ Aucun client sélectionné - utilisation des tarifs par défaut")
                return False
        else:
            # Client déjà sélectionné
            client = st.session_state.current_client
            pricing = st.session_state.get('client_pricing', {})
            
            # Afficher les infos du client sélectionné
            with st.expander("🏢 Client sélectionné", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Nom:** {client.nom}")
                    st.write(f"**Code:** {client.code_client}")
                    
                with col2:
                    st.write(f"**Type:** {client.type_client.value.capitalize()}")
                    st.write(f"**Prix:** {pricing.get('prix_kwh', 'N/A')} €/kWh")
                    
                with col3:
                    if st.button("🔄 Changer de client"):
                        # Réinitialiser la sélection
                        if 'current_client' in st.session_state:
                            del st.session_state['current_client']
                        if 'client_pricing' in st.session_state:
                            del st.session_state['client_pricing']
                        st.rerun()
                        
            return True
            
    except ImportError:
        # Module ERP non disponible
        return False
        
def get_client_price() -> Optional[float]:
    """Récupère le prix du client sélectionné.
    
    Returns:
        Prix en €/kWh ou None si pas de client sélectionné
    """
    if st.session_state.get('client_pricing'):
        return st.session_state.client_pricing.get('prix_kwh')
    return None
    
def get_client_info() -> Optional[Dict[str, Any]]:
    """Récupère les informations du client sélectionné.
    
    Returns:
        Dictionnaire avec les infos client ou None
    """
    if st.session_state.get('current_client'):
        client = st.session_state.current_client
        pricing = st.session_state.get('client_pricing', {})
        
        return {
            'id': client.id,
            'code': client.code_client,
            'nom': client.nom,
            'type': client.type_client,
            'prix_kwh': pricing.get('prix_kwh'),
            'type_tarif': pricing.get('type_tarif'),
            'zone': client.zone_geographique
        }
    return None
    
def apply_client_pricing_to_analysis(analysis_params: Dict[str, Any]) -> Dict[str, Any]:
    """Applique les tarifs du client sélectionné aux paramètres d'analyse.
    
    Args:
        analysis_params: Paramètres d'analyse actuels
        
    Returns:
        Paramètres modifiés avec les tarifs client
    """
    client_price = get_client_price()
    
    if client_price:
        # Remplacer le prix de vente par le prix client
        if 'prix_vente_electricite' in analysis_params:
            analysis_params['prix_vente_electricite_original'] = analysis_params['prix_vente_electricite']
            analysis_params['prix_vente_electricite'] = client_price
            
        # Ajouter les infos client pour le rapport
        analysis_params['client_info'] = get_client_info()
        
        # Marquer que des tarifs clients sont utilisés
        analysis_params['using_client_pricing'] = True
        
    return analysis_params