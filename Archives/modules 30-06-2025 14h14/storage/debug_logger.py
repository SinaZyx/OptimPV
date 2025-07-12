"""
Debug Logger - Système de logging avancé pour le module storage
Capture et trace toutes les opérations pour faciliter le débogage
"""

import logging
import json
import traceback
import streamlit as st
from datetime import datetime
from typing import Any, Dict, Optional, List
import pandas as pd
import numpy as np
from pathlib import Path

class StorageDebugLogger:
    """Logger spécialisé pour débugger le module storage"""
    
    def __init__(self, log_level=logging.DEBUG):
        # Configuration du logger principal
        self.logger = logging.getLogger('storage_debug')
        self.logger.setLevel(log_level)
        
        # Éviter la duplication des handlers
        if not self.logger.handlers:
            # Créer le répertoire de logs s'il n'existe pas
            self.log_dir = Path('logs/storage_debug')
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Fichier de log avec timestamp
            log_file = self.log_dir / f"storage_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            # Handler fichier avec format détaillé
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            
            # Format détaillé pour le debug
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(funcName)s | %(filename)s:%(lineno)d | %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            # Handler console pour les erreurs critiques
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)
            console_handler.setFormatter(formatter)
            
            # Ajouter les handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        # Stockage des événements pour l'interface de debug
        if 'storage_debug_events' not in st.session_state:
            st.session_state.storage_debug_events = []
    
    def log_operation(self, operation: str, data: Dict[str, Any], status: str = "START"):
        """Log une opération avec ses données"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'status': status,
            'data': self._serialize_data(data)
        }
        
        # Log dans le fichier
        self.logger.info(f"OPERATION: {json.dumps(event, default=str)}")
        
        # Stocker dans session_state pour l'UI
        if 'storage_debug_events' not in st.session_state:
            st.session_state.storage_debug_events = []
        
        if len(st.session_state.storage_debug_events) > 100:  # Limiter la taille
            st.session_state.storage_debug_events.pop(0)
        st.session_state.storage_debug_events.append(event)
        
        return event
    
    def log_error(self, operation: str, error: Exception, context: Dict[str, Any] = None):
        """Log une erreur avec contexte complet"""
        error_data = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': self._serialize_data(context or {})
        }
        
        self.logger.error(f"ERROR: {json.dumps(error_data, default=str)}")
        
        # Ajouter à l'historique des événements
        event = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'status': 'ERROR',
            'data': error_data
        }
        st.session_state.storage_debug_events.append(event)
        
        return error_data
    
    def log_data_inspection(self, data_name: str, data: Any, operation: str):
        """Inspecte et log la structure des données"""
        inspection = {
            'data_name': data_name,
            'operation': operation,
            'type': type(data).__name__,
            'inspection': self._inspect_data(data)
        }
        
        self.logger.debug(f"DATA_INSPECTION: {json.dumps(inspection, default=str)}")
        return inspection
    
    def _inspect_data(self, data: Any) -> Dict[str, Any]:
        """Inspecte la structure d'une donnée"""
        if data is None:
            return {'is_none': True}
        
        inspection = {
            'type': type(data).__name__,
            'str_repr': str(data)[:100] + '...' if len(str(data)) > 100 else str(data)
        }
        
        if isinstance(data, dict):
            inspection['keys'] = list(data.keys())
            inspection['size'] = len(data)
            # Inspecter les valeurs de premier niveau
            inspection['value_types'] = {k: type(v).__name__ for k, v in data.items()}
        
        elif isinstance(data, (list, tuple)):
            inspection['length'] = len(data)
            if data:
                inspection['first_item_type'] = type(data[0]).__name__
        
        elif isinstance(data, pd.DataFrame):
            inspection['shape'] = data.shape
            inspection['columns'] = list(data.columns)
            inspection['dtypes'] = {col: str(dtype) for col, dtype in data.dtypes.items()}
            inspection['has_na'] = data.isnull().any().any()
        
        elif isinstance(data, pd.Series):
            inspection['length'] = len(data)
            inspection['dtype'] = str(data.dtype)
            inspection['has_na'] = data.isnull().any()
        
        return inspection
    
    def _serialize_data(self, data: Any) -> Any:
        """Sérialise les données pour le logging"""
        if isinstance(data, (pd.DataFrame, pd.Series)):
            return {'type': type(data).__name__, 'shape': str(data.shape)}
        elif isinstance(data, np.ndarray):
            return {'type': 'ndarray', 'shape': str(data.shape)}
        elif isinstance(data, (datetime, pd.Timestamp)):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            return {'type': type(data).__name__, 'attrs': list(vars(data).keys())}
        else:
            try:
                json.dumps(data)
                return data
            except:
                return str(data)
    
    def export_logs(self) -> str:
        """Exporte les logs pour analyse"""
        export_data = {
            'export_time': datetime.now().isoformat(),
            'events': st.session_state.storage_debug_events,
            'session_state_keys': list(st.session_state.keys()),
            'session_state_inspection': {
                key: self._inspect_data(value) 
                for key, value in st.session_state.items() 
                if not key.startswith('_')
            }
        }
        
        export_file = self.log_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return str(export_file)
    
    def show_debug_ui(self):
        """Affiche l'interface de debug dans Streamlit"""
        with st.expander("🐛 Debug Storage Module", expanded=False):
            st.caption("Outils de débogage du module storage")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Rafraîchir", key="debug_refresh"):
                    st.rerun()
            
            with col2:
                if st.button("💾 Exporter logs", key="debug_export"):
                    export_file = self.export_logs()
                    st.success(f"Logs exportés : {export_file}")
            
            with col3:
                if st.button("🗑️ Vider logs", key="debug_clear"):
                    st.session_state.storage_debug_events = []
                    st.rerun()
            
            # Afficher les événements récents
            if st.session_state.storage_debug_events:
                st.subheader("📋 Événements récents")
                
                # Filtrer par type
                event_types = ['ALL'] + list(set(e['status'] for e in st.session_state.storage_debug_events))
                selected_type = st.selectbox("Filtrer par type", event_types, key="debug_filter")
                
                # Afficher les événements filtrés
                events_to_show = st.session_state.storage_debug_events
                if selected_type != 'ALL':
                    events_to_show = [e for e in events_to_show if e['status'] == selected_type]
                
                # Afficher en ordre inverse (plus récent en premier)
                for event in reversed(events_to_show[-20:]):  # Limiter à 20 derniers
                    status_color = {
                        'START': '🔵',
                        'SUCCESS': '✅',
                        'ERROR': '❌',
                        'WARNING': '⚠️'
                    }.get(event['status'], '⚪')
                    
                    with st.container():
                        st.markdown(f"{status_color} **{event['operation']}** - {event['timestamp']}")
                        
                        if event['status'] == 'ERROR':
                            st.error(event['data'].get('error_message', 'Unknown error'))
                            with st.expander("Détails de l'erreur"):
                                st.code(event['data'].get('traceback', 'No traceback'))
                        else:
                            with st.expander("Données"):
                                st.json(event['data'])
                        
                        st.markdown("---")
            else:
                st.info("Aucun événement de debug enregistré")

# Instance globale du logger
storage_logger = StorageDebugLogger()