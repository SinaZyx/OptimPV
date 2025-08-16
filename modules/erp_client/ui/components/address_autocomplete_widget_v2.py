"""Widget d'autocomplétion d'adresse v2 - Version professionnelle et pérenne.

Ce module fournit un widget d'autocomplétion d'adresse compatible avec les
formulaires Streamlit, conçu pour être maintenu facilement dans le temps.

Architecture:
- Séparation claire entre logique métier et présentation
- Compatible avec st.form()
- Extensible pour d'autres APIs
- Gestion d'erreurs robuste
- Performance optimisée avec cache
"""

import streamlit as st
from typing import Tuple, Optional, Dict, List, Any
import logging
from dataclasses import dataclass
from enum import Enum

from ...services.address_autocomplete import AddressAutocompleteService

logger = logging.getLogger(__name__)


class AddressFieldType(Enum):
    """Types de champs d'adresse pour une meilleure extensibilité."""
    STREET = "street"
    POSTAL_CODE = "postal_code"
    CITY = "city"
    COUNTRY = "country"
    FULL_ADDRESS = "full_address"


@dataclass
class AddressData:
    """Structure de données pour une adresse complète."""
    street: str = ""
    postal_code: str = ""
    city: str = ""
    country: str = "France"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: str = ""
    confidence_score: float = 0.0
    
    def is_complete(self) -> bool:
        """Vérifie si l'adresse contient les informations minimales."""
        return bool(self.street and self.postal_code and self.city)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour la sérialisation."""
        return {
            'street': self.street,
            'postal_code': self.postal_code,
            'city': self.city,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'formatted_address': self.formatted_address,
            'confidence_score': self.confidence_score
        }


class AddressAutocompleteWidget:
    """Widget professionnel d'autocomplétion d'adresse."""
    
    def __init__(self, 
                 service: Optional[AddressAutocompleteService] = None,
                 key_prefix: str = "address_autocomplete",
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialise le widget.
        
        Args:
            service: Service d'autocomplétion (créé par défaut si None)
            key_prefix: Préfixe pour les clés Streamlit
            config: Configuration optionnelle du widget
        """
        self.service = service or AddressAutocompleteService()
        self.key_prefix = key_prefix
        self.config = config or self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuration par défaut du widget."""
        return {
            'min_search_length': 3,
            'max_suggestions': 5,
            'show_coordinates': True,
            'show_confidence_score': True,
            'enable_manual_input': True,
            'search_delay_ms': 300,
            'placeholder_text': "Commencez à taper une adresse...",
            'no_results_text': "Aucune adresse trouvée",
            'error_text': "Erreur lors de la recherche"
        }
    
    def render(self, 
               initial_value: Optional[AddressData] = None,
               disabled: bool = False,
               required: bool = True) -> AddressData:
        """
        Affiche le widget d'autocomplétion dans un formulaire.
        
        Args:
            initial_value: Valeur initiale de l'adresse
            disabled: Désactive le widget si True
            required: Rend les champs obligatoires si True
            
        Returns:
            AddressData avec les informations saisies/sélectionnées
        """
        # Initialiser l'état si nécessaire
        self._initialize_state(initial_value)
        
        # Container principal
        container = st.container()
        
        with container:
            # Mode de saisie
            input_mode = st.radio(
                "Mode de saisie",
                ["🔍 Recherche d'adresse", "✏️ Saisie manuelle"],
                key=f"{self.key_prefix}_mode",
                horizontal=True,
                disabled=disabled
            )
            
            if input_mode == "🔍 Recherche d'adresse":
                return self._render_search_mode(disabled, required)
            else:
                return self._render_manual_mode(disabled, required)
    
    def _initialize_state(self, initial_value: Optional[AddressData]):
        """Initialise l'état du widget dans session_state."""
        state_key = f"{self.key_prefix}_state"
        
        if state_key not in st.session_state:
            st.session_state[state_key] = {
                'selected_address': initial_value or AddressData(),
                'search_query': "",
                'suggestions': [],
                'show_suggestions': False
            }
    
    def _render_search_mode(self, disabled: bool, required: bool) -> AddressData:
        """Affiche le mode recherche avec autocomplétion."""
        state_key = f"{self.key_prefix}_state"
        state = st.session_state[state_key]
        
        # Champ de recherche
        search_query = st.text_input(
            "🔍 Rechercher une adresse",
            value=state['search_query'],
            placeholder=self.config['placeholder_text'],
            key=f"{self.key_prefix}_search",
            disabled=disabled,
            help="Tapez au moins 3 caractères pour lancer la recherche"
        )
        
        # Mettre à jour la recherche si elle a changé
        if search_query != state['search_query']:
            state['search_query'] = search_query
            
            if len(search_query) >= self.config['min_search_length']:
                # Rechercher les suggestions
                try:
                    suggestions = self.service.search_addresses_dict(search_query)
                    state['suggestions'] = suggestions[:self.config['max_suggestions']]
                    state['show_suggestions'] = len(suggestions) > 0
                except Exception as e:
                    logger.error(f"Erreur recherche adresse: {e}")
                    st.error(self.config['error_text'])
                    state['suggestions'] = []
                    state['show_suggestions'] = False
            else:
                state['suggestions'] = []
                state['show_suggestions'] = False
        
        # Afficher les suggestions dans un selectbox
        if state['show_suggestions']:
            options = ["-- Sélectionnez une adresse --"] + [
                f"{s['label']} (score: {s['score']:.0%})" 
                if self.config['show_confidence_score']
                else s['label']
                for s in state['suggestions']
            ]
            
            selected_index = st.selectbox(
                "📍 Adresses trouvées",
                range(len(options)),
                format_func=lambda x: options[x],
                key=f"{self.key_prefix}_suggestions",
                disabled=disabled
            )
            
            # Si une adresse est sélectionnée
            if selected_index > 0:
                suggestion = state['suggestions'][selected_index - 1]
                state['selected_address'] = self._suggestion_to_address_data(suggestion)
        
        elif search_query and len(search_query) >= self.config['min_search_length']:
            st.info(self.config['no_results_text'])
        
        # Afficher l'adresse sélectionnée
        return self._display_selected_address(state['selected_address'], disabled)
    
    def _render_manual_mode(self, disabled: bool, required: bool) -> AddressData:
        """Affiche le mode de saisie manuelle."""
        state_key = f"{self.key_prefix}_state"
        address = st.session_state[state_key]['selected_address']
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            address.street = st.text_input(
                "Adresse",
                value=address.street,
                key=f"{self.key_prefix}_manual_street",
                disabled=disabled,
                placeholder="Numéro et nom de rue"
            )
        
        with col2:
            address.postal_code = st.text_input(
                "Code postal",
                value=address.postal_code,
                key=f"{self.key_prefix}_manual_postal",
                disabled=disabled,
                max_chars=5,
                placeholder="00000"
            )
        
        address.city = st.text_input(
            "Ville",
            value=address.city,
            key=f"{self.key_prefix}_manual_city",
            disabled=disabled,
            placeholder="Nom de la ville"
        )
        
        # Coordonnées GPS optionnelles
        if self.config['show_coordinates']:
            with st.expander("📍 Coordonnées GPS (optionnel)", expanded=False):
                col_lat, col_lon = st.columns(2)
                with col_lat:
                    address.latitude = st.number_input(
                        "Latitude",
                        value=address.latitude or 0.0,
                        min_value=-90.0,
                        max_value=90.0,
                        format="%.6f",
                        key=f"{self.key_prefix}_manual_lat",
                        disabled=disabled
                    )
                with col_lon:
                    address.longitude = st.number_input(
                        "Longitude",
                        value=address.longitude or 0.0,
                        min_value=-180.0,
                        max_value=180.0,
                        format="%.6f",
                        key=f"{self.key_prefix}_manual_lon",
                        disabled=disabled
                    )
        
        # Mettre à jour l'adresse formatée
        address.formatted_address = f"{address.street}, {address.postal_code} {address.city}".strip(", ")
        
        return address
    
    def _suggestion_to_address_data(self, suggestion: Dict[str, Any]) -> AddressData:
        """Convertit une suggestion d'API en AddressData."""
        return AddressData(
            street=suggestion.get('name', ''),
            postal_code=suggestion.get('postcode', ''),
            city=suggestion.get('city', ''),
            country="France",
            latitude=suggestion.get('lat'),
            longitude=suggestion.get('lon'),
            formatted_address=suggestion.get('label', ''),
            confidence_score=suggestion.get('score', 0.0)
        )
    
    def _display_selected_address(self, address: AddressData, disabled: bool) -> AddressData:
        """Affiche l'adresse sélectionnée avec possibilité d'édition."""
        if address.is_complete():
            st.success("✅ Adresse sélectionnée")
            
            # Afficher les détails en lecture seule
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text_input(
                    "Adresse",
                    value=address.street,
                    key=f"{self.key_prefix}_display_street",
                    disabled=True
                )
            with col2:
                st.text_input(
                    "Code postal",
                    value=address.postal_code,
                    key=f"{self.key_prefix}_display_postal",
                    disabled=True
                )
            
            st.text_input(
                "Ville",
                value=address.city,
                key=f"{self.key_prefix}_display_city",
                disabled=True
            )
            
            if self.config['show_coordinates'] and address.latitude and address.longitude:
                st.info(f"📍 GPS: {address.latitude:.6f}, {address.longitude:.6f}")
        
        return address


def render_address_autocomplete_v2(
    key_prefix: str = "address",
    initial_value: Optional[Dict[str, Any]] = None,
    disabled: bool = False,
    required: bool = True,
    config: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, str, Optional[float], Optional[float]]:
    """
    Fonction de compatibilité avec l'ancienne interface.
    
    Returns:
        Tuple (adresse, code_postal, ville, latitude, longitude)
    """
    # Créer le widget
    widget = AddressAutocompleteWidget(key_prefix=key_prefix, config=config)
    
    # Convertir la valeur initiale si fournie
    initial_address = None
    if initial_value:
        initial_address = AddressData(
            street=initial_value.get('adresse', ''),
            postal_code=initial_value.get('code_postal', ''),
            city=initial_value.get('ville', ''),
            latitude=initial_value.get('latitude'),
            longitude=initial_value.get('longitude')
        )
    
    # Afficher le widget
    result = widget.render(
        initial_value=initial_address,
        disabled=disabled,
        required=required
    )
    
    # Retourner le résultat dans le format attendu
    return (
        result.street,
        result.postal_code,
        result.city,
        result.latitude,
        result.longitude
    )