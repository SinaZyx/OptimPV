"""
Module de stockage et persistance pour les clés de répartition
"""

import json
import os
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .key_models import (
    RepartitionKey, RepartitionPeriod, RepartitionRule, 
    RepartitionTemplate, KeyType
)

logger = logging.getLogger(__name__)


class RepartitionStorage:
    """Gestionnaire de stockage pour les clés de répartition"""
    
    def __init__(self, storage_dir: str = "config/repartition_keys"):
        """
        Initialise le gestionnaire de stockage
        
        Args:
            storage_dir: Répertoire de stockage des configurations
        """
        self.storage_dir = storage_dir
        self.templates_file = os.path.join(storage_dir, "default_templates.json")
        self.rules_schema_file = os.path.join(storage_dir, "key_rules_schema.json")
        
        # Créer le répertoire si nécessaire
        os.makedirs(storage_dir, exist_ok=True)
        
        # Charger ou créer les templates par défaut
        self._ensure_default_templates()
    
    def _ensure_default_templates(self):
        """S'assure que les templates par défaut existent"""
        if not os.path.exists(self.templates_file):
            default_templates = self._create_default_templates()
            self.save_templates(default_templates)
    
    def _create_default_templates(self) -> List[RepartitionTemplate]:
        """Crée les templates par défaut"""
        templates = []
        
        # Template équitable
        templates.append(RepartitionTemplate(
            template_id="equitable",
            template_name="Répartition Équitable",
            description="Répartition équitable entre tous les participants",
            template_type="equitable",
            metadata={
                "icon": "⚖️",
                "recommended_for": ["Début de projet", "Test"],
                "created_date": datetime.now().isoformat()
            }
        ))
        
        # Template basé sur la consommation
        templates.append(RepartitionTemplate(
            template_id="consumption_based",
            template_name="Basé sur Consommation",
            description="Répartition proportionnelle à la consommation historique",
            template_type="consumption_based",
            metadata={
                "icon": "📊",
                "recommended_for": ["Optimisation économique", "Sites avec historique"],
                "created_date": datetime.now().isoformat()
            }
        ))
        
        # Template priorité PME
        templates.append(RepartitionTemplate(
            template_id="priority_pme",
            template_name="Priorité PME",
            description="Favorise les sites professionnels et PME",
            template_type="priority",
            metadata={
                "icon": "🏭",
                "recommended_for": ["Zones d'activité", "Parcs d'entreprises"],
                "created_date": datetime.now().isoformat()
            },
            rules=[
                RepartitionRule(
                    rule_id="pme_priority_1",
                    rule_name="Priorité haute PME",
                    rule_type="priority",
                    priority=100,
                    parameters={
                        "site_types": ["PME", "Professionnel"],
                        "allocation_boost": 1.5
                    },
                    enabled=True
                )
            ]
        ))
        
        # Template résidentiel
        templates.append(RepartitionTemplate(
            template_id="residential_first",
            template_name="Résidentiel Prioritaire",
            description="Priorise les sites résidentiels",
            template_type="priority",
            metadata={
                "icon": "🏠",
                "recommended_for": ["Quartiers résidentiels", "Copropriétés"],
                "created_date": datetime.now().isoformat()
            },
            rules=[
                RepartitionRule(
                    rule_id="residential_priority_1",
                    rule_name="Priorité résidentiel",
                    rule_type="priority",
                    priority=90,
                    parameters={
                        "site_types": ["Résidentiel", "Maison individuelle"],
                        "time_slots": {
                            "morning": [6, 9],
                            "evening": [18, 22]
                        }
                    },
                    enabled=True
                )
            ]
        ))
        
        return templates
    
    def save_templates(self, templates: List[RepartitionTemplate]):
        """
        Sauvegarde les templates
        
        Args:
            templates: Liste des templates à sauvegarder
        """
        try:
            templates_data = [t.to_dict() for t in templates]
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Sauvegardé {len(templates)} templates")
        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des templates: {e}")
            raise
    
    def load_templates(self) -> List[RepartitionTemplate]:
        """
        Charge tous les templates disponibles
        
        Returns:
            Liste des templates
        """
        try:
            if not os.path.exists(self.templates_file):
                return []
            
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            
            return [RepartitionTemplate.from_dict(t) for t in templates_data]
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des templates: {e}")
            return []
    
    def load_template(self, template_id: str) -> Optional[RepartitionTemplate]:
        """
        Charge un template spécifique
        
        Args:
            template_id: ID du template
            
        Returns:
            Template ou None si non trouvé
        """
        templates = self.load_templates()
        
        for template in templates:
            if template.template_id == template_id:
                return template
        
        return None
    
    def save_custom_template(self, template: RepartitionTemplate) -> bool:
        """
        Sauvegarde un template personnalisé
        
        Args:
            template: Template à sauvegarder
            
        Returns:
            True si succès
        """
        try:
            # Charger les templates existants
            templates = self.load_templates()
            
            # Remplacer ou ajouter le nouveau template
            found = False
            for i, t in enumerate(templates):
                if t.template_id == template.template_id:
                    templates[i] = template
                    found = True
                    break
            
            if not found:
                templates.append(template)
            
            # Sauvegarder
            self.save_templates(templates)
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du template personnalisé: {e}")
            return False
    
    def export_to_excel(self, keys: List[RepartitionKey], filepath: str):
        """
        Exporte les clés vers un fichier Excel
        
        Args:
            keys: Liste des clés à exporter
            filepath: Chemin du fichier Excel
        """
        try:
            # Créer un DataFrame
            data = []
            for key in keys:
                data.append({
                    'Site ID': key.site_id,
                    'Participant': key.participant_name,
                    'Allocation (%)': key.value,
                    'Type': key.key_type.value,
                    'Début': key.period_start.strftime('%Y-%m-%d') if key.period_start else '',
                    'Fin': key.period_end.strftime('%Y-%m-%d') if key.period_end else ''
                })
            
            df = pd.DataFrame(data)
            
            # Exporter vers Excel avec mise en forme
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Clés de Répartition', index=False)
                
                # Obtenir la feuille pour la mise en forme
                worksheet = writer.sheets['Clés de Répartition']
                
                # Ajuster la largeur des colonnes
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"Exporté {len(keys)} clés vers {filepath}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export Excel: {e}")
            raise
    
    def import_from_excel(self, filepath: str) -> List[RepartitionKey]:
        """
        Importe les clés depuis un fichier Excel
        
        Args:
            filepath: Chemin du fichier Excel
            
        Returns:
            Liste des clés importées
        """
        try:
            # Lire le fichier Excel
            df = pd.read_excel(filepath, sheet_name='Clés de Répartition')
            
            keys = []
            for _, row in df.iterrows():
                # Gérer les dates
                period_start = None
                period_end = None
                
                if pd.notna(row.get('Début')):
                    period_start = pd.to_datetime(row['Début'])
                if pd.notna(row.get('Fin')):
                    period_end = pd.to_datetime(row['Fin'])
                
                # Créer la clé
                key = RepartitionKey(
                    site_id=str(row['Site ID']),
                    participant_name=str(row['Participant']),
                    value=float(row['Allocation (%)']),
                    key_type=KeyType(row.get('Type', 'static')),
                    period_start=period_start,
                    period_end=period_end
                )
                keys.append(key)
            
            logger.info(f"Importé {len(keys)} clés depuis {filepath}")
            return keys
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import Excel: {e}")
            raise
    
    def save_configuration(self, config: Dict, filename: str):
        """
        Sauvegarde une configuration complète
        
        Args:
            config: Configuration à sauvegarder
            filename: Nom du fichier (sans extension)
        """
        try:
            filepath = os.path.join(self.storage_dir, f"{filename}.json")
            
            # Ajouter les métadonnées
            config['_metadata'] = {
                'saved_date': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Configuration sauvegardée: {filepath}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            raise
    
    def load_configuration(self, filename: str) -> Optional[Dict]:
        """
        Charge une configuration sauvegardée
        
        Args:
            filename: Nom du fichier (sans extension)
            
        Returns:
            Configuration ou None si non trouvée
        """
        try:
            filepath = os.path.join(self.storage_dir, f"{filename}.json")
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"Configuration chargée: {filepath}")
            return config
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            return None
    
    def list_saved_configurations(self) -> List[Dict]:
        """
        Liste toutes les configurations sauvegardées
        
        Returns:
            Liste des configurations avec métadonnées
        """
        configurations = []
        
        try:
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json') and filename != 'default_templates.json':
                    filepath = os.path.join(self.storage_dir, filename)
                    
                    # Charger les métadonnées
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        metadata = config.get('_metadata', {})
                        configurations.append({
                            'filename': filename[:-5],  # Sans .json
                            'saved_date': metadata.get('saved_date'),
                            'version': metadata.get('version', 'Unknown'),
                            'size': os.path.getsize(filepath)
                        })
                    except:
                        pass
            
            # Trier par date de sauvegarde (plus récent en premier)
            configurations.sort(
                key=lambda x: x.get('saved_date', ''), 
                reverse=True
            )
            
            return configurations
            
        except Exception as e:
            logger.error(f"Erreur lors du listage des configurations: {e}")
            return []
    
    def delete_configuration(self, filename: str) -> bool:
        """
        Supprime une configuration sauvegardée
        
        Args:
            filename: Nom du fichier (sans extension)
            
        Returns:
            True si supprimé avec succès
        """
        try:
            filepath = os.path.join(self.storage_dir, f"{filename}.json")
            
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Configuration supprimée: {filepath}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la configuration: {e}")
            return False
    
    def create_backup(self, config: Dict) -> str:
        """
        Crée une sauvegarde automatique
        
        Args:
            config: Configuration à sauvegarder
            
        Returns:
            Nom du fichier de sauvegarde
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}"
        
        self.save_configuration(config, backup_name)
        
        # Nettoyer les anciennes sauvegardes (garder les 10 dernières)
        self._cleanup_old_backups()
        
        return backup_name
    
    def _cleanup_old_backups(self, keep_count: int = 10):
        """Nettoie les anciennes sauvegardes"""
        try:
            # Lister toutes les sauvegardes
            backups = []
            for filename in os.listdir(self.storage_dir):
                if filename.startswith('backup_') and filename.endswith('.json'):
                    filepath = os.path.join(self.storage_dir, filename)
                    backups.append({
                        'filename': filename,
                        'filepath': filepath,
                        'mtime': os.path.getmtime(filepath)
                    })
            
            # Trier par date de modification
            backups.sort(key=lambda x: x['mtime'], reverse=True)
            
            # Supprimer les plus anciennes
            for backup in backups[keep_count:]:
                os.remove(backup['filepath'])
                logger.info(f"Supprimé ancienne sauvegarde: {backup['filename']}")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des sauvegardes: {e}")