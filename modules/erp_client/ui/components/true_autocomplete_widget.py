"""Widget d'autocomplétion en temps réel - Vraie autocomplétion.

Ce widget affiche des suggestions dynamiques pendant la frappe,
comme sur les sites web modernes.
"""

import streamlit as st
from typing import List, Dict, Optional, Tuple, Callable
import time
from ...services.address_autocomplete import AddressAutocompleteService


class TrueAutocompleteWidget:
    """Widget d'autocomplétion avec suggestions en temps réel."""
    
    def __init__(self, 
                 key: str = "autocomplete",
                 search_function: Optional[Callable] = None,
                 min_chars: int = 3,
                 debounce_ms: int = 300):
        """
        Initialise le widget.
        
        Args:
            key: Clé unique pour le widget
            search_function: Fonction de recherche personnalisée
            min_chars: Nombre minimum de caractères pour déclencher la recherche
            debounce_ms: Délai en ms avant de lancer la recherche
        """
        self.key = key
        self.min_chars = min_chars
        self.debounce_ms = debounce_ms
        
        # Utiliser le service d'adresse par défaut si pas de fonction fournie
        if search_function is None:
            service = AddressAutocompleteService()
            self.search_function = lambda q: service.search_addresses_dict(q, limit=5)
        else:
            self.search_function = search_function
            
        # Initialiser l'état
        self._init_state()
    
    def _init_state(self):
        """Initialise l'état du widget dans session_state."""
        if f"{self.key}_state" not in st.session_state:
            st.session_state[f"{self.key}_state"] = {
                "input_value": "",
                "last_search": "",
                "suggestions": [],
                "selected_index": -1,
                "selected_value": None,
                "last_update": 0
            }
    
    def render(self) -> Optional[Dict]:
        """
        Affiche le widget avec autocomplétion en temps réel.
        
        Returns:
            L'élément sélectionné ou None
        """
        state = st.session_state[f"{self.key}_state"]
        
        # Container pour le champ et les suggestions
        container = st.container()
        
        with container:
            # Champ de saisie
            current_value = st.text_input(
                "🔍 Recherche",
                value=state["input_value"],
                key=f"{self.key}_input",
                placeholder="Commencez à taper pour voir les suggestions...",
                label_visibility="collapsed"
            )
            
            # Détecter les changements
            if current_value != state["input_value"]:
                state["input_value"] = current_value
                state["selected_index"] = -1
                state["selected_value"] = None
                
                # Vérifier si on doit lancer une recherche
                current_time = time.time() * 1000
                if (len(current_value) >= self.min_chars and 
                    current_value != state["last_search"]):
                    
                    # Simuler un debounce simple
                    if current_time - state["last_update"] > self.debounce_ms:
                        self._perform_search(current_value)
                        state["last_update"] = current_time
                else:
                    state["suggestions"] = []
            
            # Afficher les suggestions
            if state["suggestions"] and not state["selected_value"]:
                st.markdown("### 💡 Suggestions")
                
                # Créer une liste cliquable de suggestions
                for i, suggestion in enumerate(state["suggestions"]):
                    col1, col2 = st.columns([10, 1])
                    
                    with col1:
                        # Afficher la suggestion
                        label = suggestion.get('label', '')
                        score = suggestion.get('score', 0)
                        
                        # Mettre en surbrillance la partie correspondante
                        highlighted = self._highlight_match(label, current_value)
                        
                        if st.button(
                            f"{highlighted} ({score:.0%})",
                            key=f"{self.key}_sugg_{i}",
                            use_container_width=True,
                            type="secondary"
                        ):
                            # Sélectionner cette suggestion
                            state["selected_value"] = suggestion
                            state["input_value"] = label
                            state["suggestions"] = []
                            st.rerun()
                    
                    with col2:
                        if suggestion.get('postcode'):
                            st.caption(suggestion['postcode'])
            
            # Afficher la sélection
            if state["selected_value"]:
                st.success("✅ Adresse sélectionnée")
                with st.expander("Détails de l'adresse", expanded=True):
                    selected = state["selected_value"]
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Adresse complète:**")
                        st.write(selected.get('label', ''))
                        
                        if selected.get('city'):
                            st.write("**Ville:**", selected['city'])
                        
                        if selected.get('postcode'):
                            st.write("**Code postal:**", selected['postcode'])
                    
                    with col2:
                        if selected.get('lat') and selected.get('lon'):
                            st.write("**Coordonnées GPS:**")
                            st.write(f"Latitude: {selected['lat']:.6f}")
                            st.write(f"Longitude: {selected['lon']:.6f}")
                        
                        if selected.get('score'):
                            st.write("**Confiance:**", f"{selected['score']:.0%}")
                
                # Bouton pour réinitialiser
                if st.button("🔄 Nouvelle recherche", key=f"{self.key}_reset"):
                    state["input_value"] = ""
                    state["selected_value"] = None
                    state["suggestions"] = []
                    st.rerun()
        
        return state["selected_value"]
    
    def _perform_search(self, query: str):
        """Effectue la recherche et met à jour les suggestions."""
        state = st.session_state[f"{self.key}_state"]
        
        try:
            # Appeler la fonction de recherche
            results = self.search_function(query)
            state["suggestions"] = results
            state["last_search"] = query
        except Exception as e:
            st.error(f"Erreur lors de la recherche: {e}")
            state["suggestions"] = []
    
    def _highlight_match(self, text: str, query: str) -> str:
        """Met en surbrillance la partie correspondante du texte."""
        # Simple mise en surbrillance (peut être améliorée)
        lower_text = text.lower()
        lower_query = query.lower()
        
        if lower_query in lower_text:
            start = lower_text.index(lower_query)
            end = start + len(query)
            return f"{text[:start]}**{text[start:end]}**{text[end:]}"
        
        return text


def render_true_autocomplete(
    key: str = "address_autocomplete",
    placeholder: str = "Tapez une adresse...",
    min_chars: int = 3
) -> Optional[Dict]:
    """
    Fonction helper pour afficher le widget d'autocomplétion.
    
    Args:
        key: Clé unique
        placeholder: Texte d'aide
        min_chars: Caractères minimum
        
    Returns:
        Dictionnaire avec les informations de l'adresse sélectionnée
    """
    widget = TrueAutocompleteWidget(
        key=key,
        min_chars=min_chars
    )
    
    return widget.render()


# Widget optimisé pour les formulaires
class FormCompatibleAutocomplete:
    """Version du widget compatible avec st.form()."""
    
    def __init__(self, key: str = "form_autocomplete"):
        self.key = key
        self.service = AddressAutocompleteService()
        self._init_state()
    
    def _init_state(self):
        """Initialise l'état."""
        if f"{self.key}_state" not in st.session_state:
            st.session_state[f"{self.key}_state"] = {
                "search_query": "",
                "suggestions": [],
                "selected_index": 0
            }
    
    def render_in_form(self) -> Tuple[str, str, str, Optional[float], Optional[float]]:
        """
        Affiche le widget dans un formulaire.
        
        Returns:
            Tuple (adresse, code_postal, ville, latitude, longitude)
        """
        state = st.session_state[f"{self.key}_state"]
        
        # Zone de recherche
        st.markdown("### 🔍 Recherche d'adresse")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Tapez une adresse",
                value=state["search_query"],
                key=f"{self.key}_search_input",
                placeholder="Ex: 10 rue de la Paix Paris"
            )
        
        with col2:
            # Utiliser un placeholder au lieu d'un bouton
            st.markdown("<br>", unsafe_allow_html=True)
            search_now = st.checkbox("🔍 Rechercher", key=f"{self.key}_search_check")
        
        # Lancer la recherche si demandé
        if search_now and search_query and len(search_query) >= 3:
            if search_query != state["search_query"]:
                state["search_query"] = search_query
                try:
                    results = self.service.search_addresses_dict(search_query, limit=5)
                    state["suggestions"] = results
                except Exception as e:
                    st.error(f"Erreur: {e}")
                    state["suggestions"] = []
        
        # Afficher les résultats
        if state["suggestions"]:
            st.markdown("### 📍 Résultats")
            
            # Préparer les options
            options = ["-- Sélectionnez une adresse --"] + [
                s['label'] for s in state["suggestions"]
            ]
            
            # Sélection
            selected_index = st.selectbox(
                "Choisir une adresse",
                range(len(options)),
                format_func=lambda x: options[x],
                key=f"{self.key}_select",
                index=state["selected_index"]
            )
            
            state["selected_index"] = selected_index
            
            # Si une adresse est sélectionnée
            if selected_index > 0:
                suggestion = state["suggestions"][selected_index - 1]
                
                # Afficher les détails
                with st.expander("📋 Détails de l'adresse", expanded=True):
                    st.write(f"**Rue:** {suggestion.get('name', '')}")
                    st.write(f"**Code postal:** {suggestion.get('postcode', '')}")
                    st.write(f"**Ville:** {suggestion.get('city', '')}")
                    
                    if suggestion.get('lat') and suggestion.get('lon'):
                        st.write(f"**GPS:** {suggestion['lat']:.6f}, {suggestion['lon']:.6f}")
                
                return (
                    suggestion.get('name', ''),
                    suggestion.get('postcode', ''),
                    suggestion.get('city', ''),
                    suggestion.get('lat'),
                    suggestion.get('lon')
                )
        
        # Retour par défaut
        return "", "", "", None, None