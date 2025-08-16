"""Widget Streamlit pour l'autocomplétion d'adresse.

Ce module fournit un composant réutilisable pour la saisie d'adresse
avec autocomplétion en temps réel.
"""

import streamlit as st
from typing import Optional, Dict, Tuple, Callable
import time

from ...services.address_autocomplete import get_address_service, AddressSuggestion


def render_address_autocomplete(
    key_prefix: str = "address",
    initial_address: Optional[str] = None,
    initial_postcode: Optional[str] = None,
    initial_city: Optional[str] = None,
    on_address_selected: Optional[Callable[[AddressSuggestion], None]] = None,
    show_coordinates: bool = True
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[float], Optional[float]]:
    """Affiche un widget d'autocomplétion d'adresse.
    
    Args:
        key_prefix: Préfixe pour les clés Streamlit
        initial_address: Adresse initiale
        initial_postcode: Code postal initial
        initial_city: Ville initiale
        on_address_selected: Callback appelé lors de la sélection d'une adresse
        show_coordinates: Afficher les coordonnées GPS
        
    Returns:
        Tuple (adresse, code_postal, ville, latitude, longitude)
    """
    service = get_address_service()
    
    # Initialisation des états
    if f'{key_prefix}_search_query' not in st.session_state:
        st.session_state[f'{key_prefix}_search_query'] = initial_address or ""
    if f'{key_prefix}_selected_address' not in st.session_state:
        st.session_state[f'{key_prefix}_selected_address'] = None
    if f'{key_prefix}_show_suggestions' not in st.session_state:
        st.session_state[f'{key_prefix}_show_suggestions'] = False
    
    # Container principal
    container = st.container()
    
    with container:
        # Champ de recherche d'adresse
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Input avec placeholder dynamique
            placeholder = "Commencez à taper une adresse (min. 3 caractères)..."
            if st.session_state[f'{key_prefix}_selected_address']:
                placeholder = st.session_state[f'{key_prefix}_selected_address'].display_label
            
            search_query = st.text_input(
                "🔍 Recherche d'adresse",
                value=st.session_state[f'{key_prefix}_search_query'],
                key=f"{key_prefix}_input",
                placeholder=placeholder,
                help="L'autocomplétion se déclenche après 3 caractères"
            )
            
            # Mise à jour de la requête
            if search_query != st.session_state[f'{key_prefix}_search_query']:
                st.session_state[f'{key_prefix}_search_query'] = search_query
                st.session_state[f'{key_prefix}_show_suggestions'] = len(search_query) >= 3
                if len(search_query) < 3:
                    st.session_state[f'{key_prefix}_selected_address'] = None
        
        with col2:
            # Bouton pour effacer
            if st.button("🗑️ Effacer", key=f"{key_prefix}_clear", use_container_width=True):
                st.session_state[f'{key_prefix}_search_query'] = ""
                st.session_state[f'{key_prefix}_selected_address'] = None
                st.session_state[f'{key_prefix}_show_suggestions'] = False
                st.rerun()
        
        # Zone des suggestions
        if st.session_state[f'{key_prefix}_show_suggestions'] and len(search_query) >= 3:
            with st.container():
                suggestions = service.search_addresses(
                    search_query, 
                    limit=5,
                    postcode=initial_postcode if initial_postcode and len(initial_postcode) >= 2 else None
                )
                
                if suggestions:
                    st.markdown("### 📍 Suggestions d'adresses")
                    
                    for i, suggestion in enumerate(suggestions):
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            # Affichage de la suggestion avec score
                            score_emoji = "⭐" if suggestion.score > 0.8 else "✨" if suggestion.score > 0.6 else "💫"
                            st.markdown(f"{score_emoji} **{suggestion.display_label}**")
                            if show_coordinates:
                                st.caption(f"GPS: {suggestion.latitude:.6f}, {suggestion.longitude:.6f}")
                        
                        with col2:
                            if st.button("Sélectionner", key=f"{key_prefix}_select_{i}", use_container_width=True):
                                # Enregistrer la sélection
                                st.session_state[f'{key_prefix}_selected_address'] = suggestion
                                st.session_state[f'{key_prefix}_show_suggestions'] = False
                                st.session_state[f'{key_prefix}_search_query'] = suggestion.street
                                
                                # Callback si fourni
                                if on_address_selected:
                                    on_address_selected(suggestion)
                                
                                st.rerun()
                        
                        # Séparateur entre suggestions
                        if i < len(suggestions) - 1:
                            st.markdown("---")
                else:
                    st.info("Aucune adresse trouvée. Essayez avec d'autres termes.")
        
        # Affichage de l'adresse sélectionnée
        if st.session_state[f'{key_prefix}_selected_address']:
            selected = st.session_state[f'{key_prefix}_selected_address']
            
            st.success(f"✅ Adresse sélectionnée: **{selected.display_label}**")
            
            # Détails de l'adresse dans des colonnes
            col1, col2, col3 = st.columns(3)
            
            with col1:
                adresse = st.text_input(
                    "Adresse",
                    value=selected.street,
                    key=f"{key_prefix}_street",
                    disabled=True
                )
            
            with col2:
                code_postal = st.text_input(
                    "Code postal",
                    value=selected.postcode,
                    key=f"{key_prefix}_postcode", 
                    disabled=True
                )
            
            with col3:
                ville = st.text_input(
                    "Ville",
                    value=selected.city,
                    key=f"{key_prefix}_city",
                    disabled=True
                )
            
            # Coordonnées GPS si demandées
            if show_coordinates:
                col1, col2 = st.columns(2)
                with col1:
                    latitude = st.number_input(
                        "Latitude",
                        value=selected.latitude,
                        key=f"{key_prefix}_lat",
                        disabled=True,
                        format="%.6f"
                    )
                with col2:
                    longitude = st.number_input(
                        "Longitude", 
                        value=selected.longitude,
                        key=f"{key_prefix}_lon",
                        disabled=True,
                        format="%.6f"
                    )
            else:
                latitude = selected.latitude
                longitude = selected.longitude
                
            # Zone géographique automatique
            zone = service.parse_zone_from_postcode(selected.postcode)
            st.info(f"🗺️ Zone géographique détectée: **{zone}**")
            
            return adresse, code_postal, ville, latitude, longitude
        
        # Si pas d'adresse sélectionnée, utiliser les valeurs initiales ou manuelles
        else:
            col1, col2, col3 = st.columns([3, 1, 2])
            
            with col1:
                adresse = st.text_input(
                    "Adresse",
                    value=initial_address or "",
                    key=f"{key_prefix}_street_manual"
                )
            
            with col2:
                code_postal = st.text_input(
                    "Code postal",
                    value=initial_postcode or "",
                    key=f"{key_prefix}_postcode_manual",
                    max_chars=5
                )
            
            with col3:
                ville = st.text_input(
                    "Ville",
                    value=initial_city or "",
                    key=f"{key_prefix}_city_manual"
                )
            
            # Note d'information
            if not search_query:
                st.info("💡 Commencez à taper dans le champ de recherche pour activer l'autocomplétion")
            
            return adresse, code_postal, ville, None, None


def render_simple_address_search(
    label: str = "Adresse",
    key: str = "simple_address",
    help_text: Optional[str] = None
) -> Optional[AddressSuggestion]:
    """Version simplifiée du widget d'autocomplétion pour une utilisation rapide.
    
    Args:
        label: Label du champ
        key: Clé unique pour Streamlit
        help_text: Texte d'aide
        
    Returns:
        Suggestion d'adresse sélectionnée ou None
    """
    service = get_address_service()
    
    # Input de recherche
    query = st.text_input(
        label,
        key=f"{key}_input",
        help=help_text or "Tapez au moins 3 caractères pour rechercher"
    )
    
    if len(query) >= 3:
        suggestions = service.search_addresses(query, limit=3)
        
        if suggestions:
            # Selectbox pour choisir parmi les suggestions
            options = ["Aucune sélection"] + [s.display_label for s in suggestions]
            selected_index = st.selectbox(
                "Sélectionnez une adresse",
                options=range(len(options)),
                format_func=lambda x: options[x],
                key=f"{key}_select"
            )
            
            if selected_index > 0:
                return suggestions[selected_index - 1]
    
    return None