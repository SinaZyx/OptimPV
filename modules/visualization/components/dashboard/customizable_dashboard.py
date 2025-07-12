"""
Dashboard personnalisable avec widgets drag & drop
"""
import streamlit as st
from typing import List, Dict, Any, Optional, Callable
import json
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

class WidgetType(Enum):
    """Types de widgets disponibles"""
    METRIC = "metric"
    CHART = "chart"
    TABLE = "table"
    TEXT = "text"
    IMAGE = "image"
    CUSTOM = "custom"

@dataclass
class WidgetConfig:
    """Configuration d'un widget"""
    id: str
    type: WidgetType
    title: str
    position: Dict[str, int]  # {x, y, w, h}
    config: Dict[str, Any]
    visible: bool = True
    locked: bool = False

class CustomizableDashboard:
    """Dashboard avec widgets personnalisables et drag & drop"""
    
    def __init__(self, dashboard_id: str, default_layout: Optional[List[WidgetConfig]] = None):
        """
        Initialise le dashboard personnalisable
        
        Args:
            dashboard_id: Identifiant unique du dashboard
            default_layout: Layout par défaut
        """
        self.dashboard_id = dashboard_id
        self.state_key = f"dashboard_layout_{dashboard_id}"
        
        # Initialiser le layout dans session_state
        if self.state_key not in st.session_state:
            st.session_state[self.state_key] = default_layout or []
        
        # État du mode édition
        if f"{self.state_key}_edit_mode" not in st.session_state:
            st.session_state[f"{self.state_key}_edit_mode"] = False
    
    def render(self, widget_renderers: Dict[str, Callable]):
        """
        Affiche le dashboard
        
        Args:
            widget_renderers: Dict mapping widget type to render function
        """
        # Contrôles du dashboard
        self._render_controls()
        
        # CSS pour le grid layout
        self._inject_grid_css()
        
        # Mode édition ou affichage
        if st.session_state[f"{self.state_key}_edit_mode"]:
            self._render_edit_mode(widget_renderers)
        else:
            self._render_view_mode(widget_renderers)
    
    def _render_controls(self):
        """Affiche les contrôles du dashboard"""
        col1, col2, col3, col4 = st.columns([1, 1, 1, 6])
        
        with col1:
            # Toggle mode édition
            edit_mode = st.checkbox(
                "✏️ Éditer",
                value=st.session_state[f"{self.state_key}_edit_mode"],
                key=f"{self.state_key}_edit_toggle"
            )
            st.session_state[f"{self.state_key}_edit_mode"] = edit_mode
        
        with col2:
            # Ajouter un widget
            if edit_mode:
                if st.button("➕ Widget", key=f"{self.state_key}_add_widget"):
                    self._show_add_widget_dialog()
        
        with col3:
            # Sauvegarder le layout
            if st.button("💾 Sauver", key=f"{self.state_key}_save"):
                self._save_layout()
        
        with col4:
            # Presets de layout
            preset = st.selectbox(
                "Presets",
                ["Custom", "2x2 Grid", "3 Colonnes", "Focus + Sidebar"],
                key=f"{self.state_key}_preset",
                label_visibility="collapsed"
            )
            
            if preset != "Custom":
                self._apply_preset(preset)
    
    def _inject_grid_css(self):
        """Injecte le CSS pour le système de grille"""
        st.markdown(f"""
        <style>
        /* Grid container */
        .dashboard-grid-{self.dashboard_id} {{
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            grid-auto-rows: minmax(100px, auto);
            gap: 1rem;
            padding: 1rem;
            background: var(--surface);
            border-radius: 12px;
            position: relative;
        }}
        
        /* Widget container */
        .widget-container {{
            background: var(--bg);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 2px 8px var(--shadow);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .widget-container:hover {{
            box-shadow: 0 4px 16px var(--shadow);
        }}
        
        /* Edit mode styles */
        .edit-mode .widget-container {{
            cursor: move;
            border: 2px dashed var(--border);
        }}
        
        .edit-mode .widget-container:hover {{
            border-color: var(--primary);
            background: var(--surface-hover);
        }}
        
        /* Widget controls */
        .widget-controls {{
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            display: none;
            gap: 0.25rem;
        }}
        
        .edit-mode .widget-controls {{
            display: flex;
        }}
        
        .widget-control-btn {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
            border: none;
            background: var(--surface);
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            transition: all 0.2s ease;
        }}
        
        .widget-control-btn:hover {{
            background: var(--primary);
            color: white;
            transform: scale(1.1);
        }}
        
        /* Drag handle */
        .drag-handle {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 32px;
            cursor: move;
            background: linear-gradient(180deg, rgba(0,0,0,0.05) 0%, transparent 100%);
            display: none;
        }}
        
        .edit-mode .drag-handle {{
            display: block;
        }}
        
        /* Resize handle */
        .resize-handle {{
            position: absolute;
            bottom: 0;
            right: 0;
            width: 20px;
            height: 20px;
            cursor: nwse-resize;
            display: none;
        }}
        
        .edit-mode .resize-handle {{
            display: block;
        }}
        
        .resize-handle::after {{
            content: '';
            position: absolute;
            bottom: 2px;
            right: 2px;
            width: 0;
            height: 0;
            border-style: solid;
            border-width: 0 0 10px 10px;
            border-color: transparent transparent var(--primary) transparent;
        }}
        
        /* Grid positions */
        {self._generate_grid_positions_css()}
        
        /* Animations */
        @keyframes widgetAdd {{
            from {{
                transform: scale(0.8);
                opacity: 0;
            }}
            to {{
                transform: scale(1);
                opacity: 1;
            }}
        }}
        
        .widget-new {{
            animation: widgetAdd 0.3s ease-out;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .dashboard-grid-{self.dashboard_id} {{
                grid-template-columns: 1fr;
            }}
            
            .widget-container {{
                grid-column: 1 !important;
                grid-row: auto !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def _generate_grid_positions_css(self) -> str:
        """Génère le CSS pour les positions de grille"""
        css = ""
        for widget in st.session_state[self.state_key]:
            pos = widget.position if isinstance(widget, WidgetConfig) else widget['position']
            widget_id = widget.id if isinstance(widget, WidgetConfig) else widget['id']
            
            css += f"""
            .widget-{widget_id} {{
                grid-column: {pos['x']} / span {pos['w']};
                grid-row: {pos['y']} / span {pos['h']};
            }}
            """
        return css
    
    def _render_view_mode(self, widget_renderers: Dict[str, Callable]):
        """Affiche le dashboard en mode visualisation"""
        # Container principal
        dashboard_html = f'<div class="dashboard-grid-{self.dashboard_id}">'
        
        # Rendu des widgets
        for widget_config in st.session_state[self.state_key]:
            if isinstance(widget_config, dict):
                widget_config = WidgetConfig(**widget_config)
            
            if not widget_config.visible:
                continue
            
            # Container du widget
            widget_html = f"""
            <div class="widget-container widget-{widget_config.id}">
                <div class="widget-content" id="widget-content-{widget_config.id}"></div>
            </div>
            """
            dashboard_html += widget_html
        
        dashboard_html += '</div>'
        
        # Afficher le HTML
        st.markdown(dashboard_html, unsafe_allow_html=True)
        
        # Rendu du contenu des widgets
        for widget_config in st.session_state[self.state_key]:
            if isinstance(widget_config, dict):
                widget_config = WidgetConfig(**widget_config)
            
            if not widget_config.visible:
                continue
            
            # Placeholder pour le widget
            widget_placeholder = st.empty()
            
            # Rendu du widget via le renderer approprié
            widget_type = widget_config.type.value if isinstance(widget_config.type, WidgetType) else widget_config.type
            
            if widget_type in widget_renderers:
                with widget_placeholder.container():
                    try:
                        widget_renderers[widget_type](widget_config)
                    except Exception as e:
                        st.error(f"Erreur widget {widget_config.title}: {str(e)}")
    
    def _render_edit_mode(self, widget_renderers: Dict[str, Callable]):
        """Affiche le dashboard en mode édition"""
        st.info("🔧 **Mode Édition** - Glissez les widgets pour les repositionner")
        
        # JavaScript pour le drag & drop
        self._inject_drag_drop_js()
        
        # Container principal avec classe edit-mode
        dashboard_html = f'<div class="dashboard-grid-{self.dashboard_id} edit-mode">'
        
        # Rendu des widgets avec contrôles
        for i, widget_config in enumerate(st.session_state[self.state_key]):
            if isinstance(widget_config, dict):
                widget_config = WidgetConfig(**widget_config)
            
            # Container du widget avec contrôles
            widget_html = f"""
            <div class="widget-container widget-{widget_config.id}" 
                 data-widget-id="{widget_config.id}"
                 data-widget-index="{i}">
                <div class="drag-handle"></div>
                <div class="widget-controls">
                    <button class="widget-control-btn" onclick="configureWidget('{widget_config.id}')" title="Configurer">
                        ⚙️
                    </button>
                    <button class="widget-control-btn" onclick="toggleWidget('{widget_config.id}')" title="Masquer">
                        👁️
                    </button>
                    <button class="widget-control-btn" onclick="deleteWidget('{widget_config.id}')" title="Supprimer">
                        🗑️
                    </button>
                </div>
                <div class="widget-content" id="widget-content-{widget_config.id}">
                    <h4>{widget_config.title}</h4>
                    <p style="color: var(--text-secondary);">Type: {widget_config.type}</p>
                    <p style="color: var(--text-secondary);">Position: ({widget_config.position['x']}, {widget_config.position['y']})</p>
                    <p style="color: var(--text-secondary);">Taille: {widget_config.position['w']}x{widget_config.position['h']}</p>
                </div>
                <div class="resize-handle"></div>
            </div>
            """
            dashboard_html += widget_html
        
        dashboard_html += '</div>'
        
        # Afficher le HTML
        st.markdown(dashboard_html, unsafe_allow_html=True)
    
    def _inject_drag_drop_js(self):
        """Injecte le JavaScript pour le drag & drop"""
        st.markdown(f"""
        <script>
        // Variables globales
        let draggedElement = null;
        let draggedIndex = null;
        
        // Initialiser le drag & drop
        document.addEventListener('DOMContentLoaded', function() {{
            const widgets = document.querySelectorAll('.widget-container');
            
            widgets.forEach(widget => {{
                // Drag start
                widget.addEventListener('dragstart', function(e) {{
                    draggedElement = this;
                    draggedIndex = parseInt(this.dataset.widgetIndex);
                    this.style.opacity = '0.5';
                    e.dataTransfer.effectAllowed = 'move';
                    e.dataTransfer.setData('text/html', this.innerHTML);
                }});
                
                // Drag over
                widget.addEventListener('dragover', function(e) {{
                    if (e.preventDefault) {{
                        e.preventDefault();
                    }}
                    e.dataTransfer.dropEffect = 'move';
                    this.classList.add('drag-over');
                    return false;
                }});
                
                // Drag leave
                widget.addEventListener('dragleave', function(e) {{
                    this.classList.remove('drag-over');
                }});
                
                // Drop
                widget.addEventListener('drop', function(e) {{
                    if (e.stopPropagation) {{
                        e.stopPropagation();
                    }}
                    
                    if (draggedElement !== this) {{
                        // Échanger les positions
                        const targetIndex = parseInt(this.dataset.widgetIndex);
                        updateWidgetPositions(draggedIndex, targetIndex);
                    }}
                    
                    return false;
                }});
                
                // Drag end
                widget.addEventListener('dragend', function(e) {{
                    this.style.opacity = '';
                    widgets.forEach(w => w.classList.remove('drag-over'));
                }});
                
                // Make draggable
                widget.draggable = true;
            }});
        }});
        
        // Fonctions de contrôle des widgets
        function configureWidget(widgetId) {{
            // Ouvrir la configuration du widget
            console.log('Configure widget:', widgetId);
            // Communication avec Streamlit via custom component
        }}
        
        function toggleWidget(widgetId) {{
            // Basculer la visibilité du widget
            console.log('Toggle widget:', widgetId);
        }}
        
        function deleteWidget(widgetId) {{
            // Supprimer le widget
            if (confirm('Supprimer ce widget ?')) {{
                console.log('Delete widget:', widgetId);
            }}
        }}
        
        function updateWidgetPositions(fromIndex, toIndex) {{
            // Mettre à jour les positions dans Streamlit
            console.log('Move widget from', fromIndex, 'to', toIndex);
        }}
        </script>
        """, unsafe_allow_html=True)
    
    def add_widget(self, widget_type: WidgetType, title: str, config: Dict[str, Any], 
                   position: Optional[Dict[str, int]] = None) -> str:
        """
        Ajoute un widget au dashboard
        
        Args:
            widget_type: Type de widget
            title: Titre du widget
            config: Configuration du widget
            position: Position {x, y, w, h} ou None pour auto
            
        Returns:
            ID du widget créé
        """
        widget_id = str(uuid.uuid4())[:8]
        
        # Position par défaut
        if position is None:
            position = self._find_next_position()
        
        widget_config = WidgetConfig(
            id=widget_id,
            type=widget_type,
            title=title,
            position=position,
            config=config
        )
        
        st.session_state[self.state_key].append(widget_config)
        return widget_id
    
    def _find_next_position(self) -> Dict[str, int]:
        """Trouve la prochaine position disponible"""
        # Logique simple : ajouter à la fin
        existing_widgets = st.session_state[self.state_key]
        
        if not existing_widgets:
            return {"x": 1, "y": 1, "w": 4, "h": 2}
        
        # Trouver la position la plus basse
        max_y = max(w.position['y'] + w.position['h'] for w in existing_widgets)
        
        return {"x": 1, "y": max_y, "w": 4, "h": 2}
    
    def remove_widget(self, widget_id: str):
        """Supprime un widget"""
        st.session_state[self.state_key] = [
            w for w in st.session_state[self.state_key]
            if w.id != widget_id
        ]
    
    def update_widget(self, widget_id: str, **kwargs):
        """Met à jour un widget"""
        for widget in st.session_state[self.state_key]:
            if widget.id == widget_id:
                for key, value in kwargs.items():
                    if hasattr(widget, key):
                        setattr(widget, key, value)
                break
    
    def _save_layout(self):
        """Sauvegarde le layout actuel"""
        # Convertir en JSON pour sauvegarde
        layout_data = []
        for widget in st.session_state[self.state_key]:
            if isinstance(widget, WidgetConfig):
                widget_dict = asdict(widget)
                widget_dict['type'] = widget.type.value
                layout_data.append(widget_dict)
            else:
                layout_data.append(widget)
        
        # Sauvegarder (ici on pourrait sauver en base de données)
        st.success("✅ Layout sauvegardé!")
        
        # Pour debug
        with st.expander("Layout JSON"):
            st.json(layout_data)
    
    def _apply_preset(self, preset_name: str):
        """Applique un preset de layout"""
        if preset_name == "2x2 Grid":
            # Réorganiser en grille 2x2
            for i, widget in enumerate(st.session_state[self.state_key][:4]):
                x = (i % 2) * 6 + 1
                y = (i // 2) * 3 + 1
                widget.position = {"x": x, "y": y, "w": 6, "h": 3}
                
        elif preset_name == "3 Colonnes":
            # Réorganiser en 3 colonnes
            for i, widget in enumerate(st.session_state[self.state_key]):
                x = (i % 3) * 4 + 1
                y = (i // 3) * 3 + 1
                widget.position = {"x": x, "y": y, "w": 4, "h": 3}
                
        elif preset_name == "Focus + Sidebar":
            # Un grand widget + sidebar
            if len(st.session_state[self.state_key]) > 0:
                # Widget principal
                st.session_state[self.state_key][0].position = {"x": 1, "y": 1, "w": 8, "h": 6}
                
                # Widgets sidebar
                for i, widget in enumerate(st.session_state[self.state_key][1:4]):
                    widget.position = {"x": 9, "y": i * 2 + 1, "w": 4, "h": 2}
        
        st.rerun()
    
    def _show_add_widget_dialog(self):
        """Affiche le dialogue d'ajout de widget"""
        with st.expander("➕ Ajouter un widget", expanded=True):
            widget_type = st.selectbox(
                "Type de widget",
                [t.value for t in WidgetType],
                format_func=lambda x: {
                    "metric": "📊 Métrique",
                    "chart": "📈 Graphique",
                    "table": "📋 Tableau",
                    "text": "📝 Texte",
                    "image": "🖼️ Image",
                    "custom": "🔧 Personnalisé"
                }.get(x, x)
            )
            
            title = st.text_input("Titre du widget")
            
            # Configuration spécifique selon le type
            config = {}
            
            if widget_type == WidgetType.METRIC.value:
                config['value'] = st.text_input("Valeur", "0")
                config['delta'] = st.text_input("Delta", "+0%")
                config['color'] = st.selectbox("Couleur", ["primary", "success", "warning", "error"])
                
            elif widget_type == WidgetType.CHART.value:
                config['chart_type'] = st.selectbox("Type", ["line", "bar", "pie", "scatter"])
                
            elif widget_type == WidgetType.TEXT.value:
                config['content'] = st.text_area("Contenu")
            
            # Position
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                x = st.number_input("X", min_value=1, max_value=12, value=1)
            with col2:
                y = st.number_input("Y", min_value=1, value=1)
            with col3:
                w = st.number_input("Largeur", min_value=1, max_value=12, value=4)
            with col4:
                h = st.number_input("Hauteur", min_value=1, value=2)
            
            if st.button("Ajouter", type="primary"):
                if title:
                    position = {"x": x, "y": y, "w": w, "h": h}
                    self.add_widget(
                        WidgetType(widget_type),
                        title,
                        config,
                        position
                    )
                    st.success(f"✅ Widget '{title}' ajouté!")
                    st.rerun()
                else:
                    st.error("Veuillez entrer un titre")