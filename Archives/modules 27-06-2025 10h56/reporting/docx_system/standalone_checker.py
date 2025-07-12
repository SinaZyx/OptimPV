"""
Vérificateur autonome du système DOCX
Peut être importé sans dépendances Streamlit
"""

import os
import sys
from typing import Dict, Any


class DocxSystemChecker:
    """Vérifie l'état du système DOCX sans dépendances externes"""
    
    @staticmethod
    def check_system_status() -> Dict[str, Any]:
        """Vérifie le statut du système DOCX de manière autonome"""
        status = {
            'dependency_manager_available': False,
            'docx_system_available': False,
            'files_present': False,
            'can_import_manager': False,
            'missing_dependencies': [],
            'error_message': None
        }
        
        # Vérifier que les fichiers existent
        base_path = os.path.dirname(os.path.abspath(__file__))
        required_files = [
            'dependency_manager.py',
            'template_generator.py',
            'data_extractor.py',
            'chart_generator.py'
        ]
        
        all_files_present = all(
            os.path.exists(os.path.join(base_path, f)) 
            for f in required_files
        )
        status['files_present'] = all_files_present
        
        # Essayer d'importer le dependency_manager
        try:
            # Import direct sans passer par le module parent
            sys.path.insert(0, base_path)
            from dependency_manager import DocxDependencyManager
            status['dependency_manager_available'] = True
            status['can_import_manager'] = True
            
            # Créer une instance et vérifier les dépendances
            manager = DocxDependencyManager()
            status['missing_dependencies'] = manager.get_missing_dependencies()
            status['docx_system_available'] = manager.is_system_ready()
            
        except ImportError as e:
            status['error_message'] = str(e)
        except Exception as e:
            status['error_message'] = f"Erreur initialisation: {str(e)}"
        finally:
            # Nettoyer sys.path
            if base_path in sys.path:
                sys.path.remove(base_path)
        
        return status
    
    @staticmethod
    def get_quick_status() -> bool:
        """Retourne True si le système DOCX peut être utilisé"""
        try:
            status = DocxSystemChecker.check_system_status()
            return status['dependency_manager_available']
        except:
            return False