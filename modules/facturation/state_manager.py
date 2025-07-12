"""
State Manager for PMO Billing System
Advanced state management with cache, auto-save, and offline capabilities
"""

import streamlit as st
import json
import pickle
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
import threading
import uuid
from pathlib import Path
import os


class StateManager:
    """Advanced state management for the billing system"""
    
    def __init__(self):
        self.init_state()
        self.cache_dir = self._get_cache_dir()
        self.auto_save_interval = 30  # seconds
        self.last_auto_save = {}
        
    def init_state(self):
        """Initialize all state variables"""
        default_states = {
            'user_preferences': {
                'theme': 'OptimPV Corporate',
                'language': 'fr',
                'auto_save': True,
                'notifications': True,
                'animations': True,
                'compact_mode': False
            },
            'session_data': {},
            'cache': {},
            'undo_stack': [],
            'redo_stack': [],
            'auto_save_data': {},
            'offline_queue': [],
            'search_history': [],
            'recent_actions': [],
            'bookmarks': [],
            'quick_filters': {},
            'column_preferences': {},
            'dashboard_layout': 'default'
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value
    
    def _get_cache_dir(self) -> Path:
        """Get cache directory path"""
        if os.name == 'nt':  # Windows
            cache_dir = Path(os.environ.get('APPDATA', '')) / 'OptimPV' / 'facturation_cache'
        else:  # Unix/Linux/Mac
            cache_dir = Path.home() / '.optimpv' / 'facturation_cache'
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def set_user_preference(self, key: str, value: Any):
        """Set user preference with auto-save"""
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
        
        st.session_state.user_preferences[key] = value
        self._save_preferences_to_disk()
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        return st.session_state.get('user_preferences', {}).get(key, default)
    
    def _save_preferences_to_disk(self):
        """Save preferences to disk"""
        try:
            prefs_file = self.cache_dir / 'user_preferences.json'
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.get('user_preferences', {}), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving preferences: {e}")
    
    def load_preferences_from_disk(self):
        """Load preferences from disk"""
        try:
            prefs_file = self.cache_dir / 'user_preferences.json'
            if prefs_file.exists():
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    st.session_state.user_preferences = json.load(f)
        except Exception as e:
            print(f"Error loading preferences: {e}")
    
    def cache_data(self, key: str, data: Any, ttl: int = 3600):
        """Cache data with TTL (Time To Live)"""
        if 'cache' not in st.session_state:
            st.session_state.cache = {}
        
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        st.session_state.cache[key] = {
            'data': data,
            'expiry': expiry_time,
            'created': datetime.now(),
            'access_count': 0
        }
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        if 'cache' not in st.session_state:
            return None
        
        cached_item = st.session_state.cache.get(key)
        if not cached_item:
            return None
        
        # Check expiry
        if datetime.now() > cached_item['expiry']:
            # Remove expired item
            del st.session_state.cache[key]
            return None
        
        # Update access count
        cached_item['access_count'] += 1
        return cached_item['data']
    
    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache, optionally by pattern"""
        if 'cache' not in st.session_state:
            return 0
        
        if pattern is None:
            # Clear all cache
            count = len(st.session_state.cache)
            st.session_state.cache.clear()
            return count
        
        # Clear cache matching pattern
        keys_to_remove = [key for key in st.session_state.cache.keys() if pattern in key]
        for key in keys_to_remove:
            del st.session_state.cache[key]
        
        return len(keys_to_remove)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if 'cache' not in st.session_state:
            return {'total_items': 0, 'memory_usage_kb': 0, 'hit_rate': 0}
        
        cache = st.session_state.cache
        total_items = len(cache)
        
        # Estimate memory usage (rough approximation)
        total_size = 0
        total_access = 0
        
        for item in cache.values():
            total_size += len(str(item['data']))  # Rough size estimation
            total_access += item['access_count']
        
        memory_usage_kb = total_size / 1024
        
        return {
            'total_items': total_items,
            'memory_usage_kb': memory_usage_kb,
            'total_access': total_access,
            'avg_access_per_item': total_access / max(1, total_items)
        }
    
    def add_to_undo_stack(self, action: Dict[str, Any]):
        """Add action to undo stack"""
        if 'undo_stack' not in st.session_state:
            st.session_state.undo_stack = []
        
        # Limit undo stack size
        max_undo_size = 50
        if len(st.session_state.undo_stack) >= max_undo_size:
            st.session_state.undo_stack.pop(0)
        
        action['timestamp'] = datetime.now()
        action['id'] = str(uuid.uuid4())
        st.session_state.undo_stack.append(action)
        
        # Clear redo stack when new action is performed
        st.session_state.redo_stack = []
    
    def undo_last_action(self) -> Optional[Dict[str, Any]]:
        """Undo last action"""
        if not st.session_state.get('undo_stack'):
            return None
        
        action = st.session_state.undo_stack.pop()
        
        # Add to redo stack
        if 'redo_stack' not in st.session_state:
            st.session_state.redo_stack = []
        st.session_state.redo_stack.append(action)
        
        return action
    
    def redo_last_action(self) -> Optional[Dict[str, Any]]:
        """Redo last undone action"""
        if not st.session_state.get('redo_stack'):
            return None
        
        action = st.session_state.redo_stack.pop()
        st.session_state.undo_stack.append(action)
        
        return action
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return bool(st.session_state.get('undo_stack'))
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return bool(st.session_state.get('redo_stack'))
    
    def auto_save_form_data(self, form_id: str, data: Dict[str, Any]):
        """Auto-save form data"""
        if not self.get_user_preference('auto_save', True):
            return
        
        current_time = datetime.now()
        
        # Check if enough time has passed since last save
        if form_id in self.last_auto_save:
            time_diff = (current_time - self.last_auto_save[form_id]).total_seconds()
            if time_diff < self.auto_save_interval:
                return
        
        # Save form data
        if 'auto_save_data' not in st.session_state:
            st.session_state.auto_save_data = {}
        
        st.session_state.auto_save_data[form_id] = {
            'data': data,
            'timestamp': current_time,
            'version': 1  # For future versioning
        }
        
        self.last_auto_save[form_id] = current_time
        
        # Save to disk as well
        self._save_auto_save_to_disk()
    
    def get_auto_saved_data(self, form_id: str) -> Optional[Dict[str, Any]]:
        """Get auto-saved form data"""
        auto_save_data = st.session_state.get('auto_save_data', {})
        return auto_save_data.get(form_id, {}).get('data')
    
    def _save_auto_save_to_disk(self):
        """Save auto-save data to disk"""
        try:
            auto_save_file = self.cache_dir / 'auto_save.json'
            
            # Convert datetime objects to strings for JSON serialization
            serializable_data = {}
            for form_id, form_data in st.session_state.get('auto_save_data', {}).items():
                serializable_data[form_id] = {
                    'data': form_data['data'],
                    'timestamp': form_data['timestamp'].isoformat(),
                    'version': form_data['version']
                }
            
            with open(auto_save_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error saving auto-save data: {e}")
    
    def load_auto_save_from_disk(self):
        """Load auto-save data from disk"""
        try:
            auto_save_file = self.cache_dir / 'auto_save.json'
            if auto_save_file.exists():
                with open(auto_save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert timestamp strings back to datetime objects
                for form_id, form_data in data.items():
                    form_data['timestamp'] = datetime.fromisoformat(form_data['timestamp'])
                
                st.session_state.auto_save_data = data
        except Exception as e:
            print(f"Error loading auto-save data: {e}")
    
    def add_to_recent_actions(self, action: Dict[str, Any]):
        """Add action to recent actions list"""
        if 'recent_actions' not in st.session_state:
            st.session_state.recent_actions = []
        
        action['timestamp'] = datetime.now()
        st.session_state.recent_actions.insert(0, action)
        
        # Limit recent actions to 100
        if len(st.session_state.recent_actions) > 100:
            st.session_state.recent_actions = st.session_state.recent_actions[:100]
    
    def get_recent_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent actions"""
        return st.session_state.get('recent_actions', [])[:limit]
    
    def add_search_to_history(self, search_term: str, context: str = 'general'):
        """Add search term to history"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        
        search_entry = {
            'term': search_term,
            'context': context,
            'timestamp': datetime.now()
        }
        
        # Remove duplicates
        st.session_state.search_history = [
            entry for entry in st.session_state.search_history 
            if not (entry['term'] == search_term and entry['context'] == context)
        ]
        
        st.session_state.search_history.insert(0, search_entry)
        
        # Limit search history
        if len(st.session_state.search_history) > 50:
            st.session_state.search_history = st.session_state.search_history[:50]
    
    def get_search_suggestions(self, context: str = 'general', limit: int = 5) -> List[str]:
        """Get search suggestions based on history"""
        search_history = st.session_state.get('search_history', [])
        
        # Filter by context and get unique terms
        suggestions = []
        for entry in search_history:
            if entry['context'] == context and entry['term'] not in suggestions:
                suggestions.append(entry['term'])
            
            if len(suggestions) >= limit:
                break
        
        return suggestions
    
    def add_bookmark(self, name: str, page: str, filters: Dict[str, Any] = None):
        """Add bookmark for quick navigation"""
        if 'bookmarks' not in st.session_state:
            st.session_state.bookmarks = []
        
        bookmark = {
            'id': str(uuid.uuid4()),
            'name': name,
            'page': page,
            'filters': filters or {},
            'created': datetime.now()
        }
        
        st.session_state.bookmarks.append(bookmark)
    
    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """Get all bookmarks"""
        return st.session_state.get('bookmarks', [])
    
    def remove_bookmark(self, bookmark_id: str) -> bool:
        """Remove bookmark by ID"""
        if 'bookmarks' not in st.session_state:
            return False
        
        original_length = len(st.session_state.bookmarks)
        st.session_state.bookmarks = [
            bm for bm in st.session_state.bookmarks if bm['id'] != bookmark_id
        ]
        
        return len(st.session_state.bookmarks) < original_length
    
    def set_quick_filter(self, context: str, filter_name: str, filter_value: Any):
        """Set a quick filter for easy reuse"""
        if 'quick_filters' not in st.session_state:
            st.session_state.quick_filters = {}
        
        if context not in st.session_state.quick_filters:
            st.session_state.quick_filters[context] = {}
        
        st.session_state.quick_filters[context][filter_name] = {
            'value': filter_value,
            'created': datetime.now(),
            'usage_count': st.session_state.quick_filters[context].get(filter_name, {}).get('usage_count', 0) + 1
        }
    
    def get_quick_filters(self, context: str) -> Dict[str, Any]:
        """Get quick filters for a context"""
        return st.session_state.get('quick_filters', {}).get(context, {})
    
    def set_column_preferences(self, table_id: str, preferences: Dict[str, Any]):
        """Set column preferences for a table"""
        if 'column_preferences' not in st.session_state:
            st.session_state.column_preferences = {}
        
        st.session_state.column_preferences[table_id] = preferences
    
    def get_column_preferences(self, table_id: str) -> Dict[str, Any]:
        """Get column preferences for a table"""
        return st.session_state.get('column_preferences', {}).get(table_id, {})
    
    def add_to_offline_queue(self, action: Dict[str, Any]):
        """Add action to offline queue for later processing"""
        if 'offline_queue' not in st.session_state:
            st.session_state.offline_queue = []
        
        action['queued_at'] = datetime.now()
        action['id'] = str(uuid.uuid4())
        st.session_state.offline_queue.append(action)
    
    def process_offline_queue(self) -> List[Dict[str, Any]]:
        """Process and clear offline queue"""
        queue = st.session_state.get('offline_queue', [])
        st.session_state.offline_queue = []
        return queue
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        start_time = st.session_state.get('session_start_time', datetime.now())
        
        return {
            'session_duration': str(datetime.now() - start_time),
            'actions_performed': len(st.session_state.get('recent_actions', [])),
            'cache_items': len(st.session_state.get('cache', {})),
            'auto_saves': len(st.session_state.get('auto_save_data', {})),
            'searches_performed': len(st.session_state.get('search_history', [])),
            'bookmarks_created': len(st.session_state.get('bookmarks', [])),
            'offline_queue_size': len(st.session_state.get('offline_queue', [])),
            'undo_available': len(st.session_state.get('undo_stack', [])),
            'redo_available': len(st.session_state.get('redo_stack', []))
        }
    
    def export_session_data(self) -> str:
        """Export session data as JSON"""
        export_data = {
            'user_preferences': st.session_state.get('user_preferences', {}),
            'bookmarks': st.session_state.get('bookmarks', []),
            'search_history': st.session_state.get('search_history', []),
            'quick_filters': st.session_state.get('quick_filters', {}),
            'column_preferences': st.session_state.get('column_preferences', {}),
            'exported_at': datetime.now().isoformat()
        }
        
        return json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    
    def import_session_data(self, json_data: str) -> bool:
        """Import session data from JSON"""
        try:
            data = json.loads(json_data)
            
            # Import each section
            if 'user_preferences' in data:
                st.session_state.user_preferences.update(data['user_preferences'])
            
            if 'bookmarks' in data:
                # Convert datetime strings back to datetime objects
                for bookmark in data['bookmarks']:
                    bookmark['created'] = datetime.fromisoformat(bookmark['created'])
                st.session_state.bookmarks.extend(data['bookmarks'])
            
            if 'search_history' in data:
                for entry in data['search_history']:
                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                st.session_state.search_history.extend(data['search_history'])
            
            if 'quick_filters' in data:
                st.session_state.quick_filters.update(data['quick_filters'])
            
            if 'column_preferences' in data:
                st.session_state.column_preferences.update(data['column_preferences'])
            
            return True
            
        except Exception as e:
            print(f"Error importing session data: {e}")
            return False
    
    def cleanup_expired_cache(self):
        """Clean up expired cache items"""
        if 'cache' not in st.session_state:
            return 0
        
        current_time = datetime.now()
        expired_keys = []
        
        for key, item in st.session_state.cache.items():
            if current_time > item['expiry']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del st.session_state.cache[key]
        
        return len(expired_keys)
    
    def schedule_background_tasks(self):
        """Schedule background tasks (if needed)"""
        # This would be used for periodic cleanup, auto-save, etc.
        # In Streamlit, we rely on user interactions to trigger these
        pass


# Global state manager instance
state_manager = StateManager()