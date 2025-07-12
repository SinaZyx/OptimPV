"""
Gestionnaire principal des clés de répartition
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import copy
import logging

# Import conditionnel de Streamlit
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    # Créer une classe mock pour session_state en mode test
    class MockSessionState:
        def __init__(self):
            self._state = {}
        
        def __contains__(self, key):
            return key in self._state
        
        def __getattr__(self, key):
            return self._state.get(key, None)
        
        def __setattr__(self, key, value):
            if key == '_state':
                super().__setattr__(key, value)
            else:
                self._state[key] = value
    
    class MockStreamlit:
        session_state = MockSessionState()
    
    st = MockStreamlit()

from .key_models import (
    RepartitionKey, RepartitionPeriod, RepartitionRule, 
    RepartitionTemplate, KeyType, PeriodType
)
from .key_validators import RepartitionValidator
from .key_calculations import (
    apply_static_keys, apply_temporal_keys, apply_dynamic_rules,
    optimize_repartition
)
from .key_storage import RepartitionStorage

logger = logging.getLogger(__name__)


class RepartitionKeyManager:
    """Gestionnaire principal pour les clés de répartition"""
    
    def __init__(self, sites_config: Dict):
        """
        Initialise le gestionnaire avec la configuration des sites
        
        Args:
            sites_config: Configuration des sites depuis session_state
        """
        self.sites_config = sites_config
        self.validator = RepartitionValidator()
        self.storage = RepartitionStorage()
        
        # Initialiser l'état dans session_state si nécessaire
        if 'repartition_config' not in st.session_state:
            st.session_state.repartition_config = self._get_default_config()
        
        self.config = st.session_state.repartition_config
        
        # Initialiser les clés par défaut si nécessaire
        if not self.config.get('current_keys'):
            self._initialize_default_keys()
        
        # Historique des configurations
        if 'repartition_history' not in st.session_state:
            st.session_state.repartition_history = []
        
        logger.info(f"RepartitionKeyManager initialisé avec {len(self.sites_config)} sites")
    
    def update_sites_config(self, new_sites_config: Dict):
        """
        Met à jour la configuration des sites et ajuste les clés si nécessaire
        
        Args:
            new_sites_config: Nouvelle configuration des sites
        """
        # Détecter les nouveaux sites
        old_sites = set(self.sites_config.keys())
        new_sites = set(new_sites_config.keys())
        added_sites = new_sites - old_sites
        removed_sites = old_sites - new_sites
        
        # Mettre à jour la configuration
        self.sites_config = new_sites_config
        
        # Si des sites ont été ajoutés ou supprimés, ajuster les clés
        if added_sites or removed_sites:
            logger.info(f"Sites modifiés - Ajoutés: {added_sites}, Supprimés: {removed_sites}")
            
            # Obtenir les clés actuelles
            current_keys = self.get_current_keys()
            
            # Filtrer les clés pour les sites supprimés
            updated_keys = [k for k in current_keys if k.site_id not in removed_sites]
            
            # Ajouter des clés pour les nouveaux sites
            if added_sites:
                # Calculer la répartition pour les nouveaux sites
                total_current = sum(k.value for k in updated_keys)
                remaining = 100.0 - total_current
                
                if remaining > 0 and len(added_sites) > 0:
                    # Répartir équitablement le reste entre les nouveaux sites
                    value_per_new_site = remaining / len(added_sites)
                else:
                    # Si pas de place, redistribuer équitablement entre tous
                    all_sites_count = len(new_sites_config)
                    value_per_site = 100.0 / all_sites_count if all_sites_count > 0 else 0
                    
                    # Recréer toutes les clés
                    updated_keys = []
                    for site_id, site_data in new_sites_config.items():
                        key = RepartitionKey(
                            site_id=site_id,
                            participant_name=site_data.get('nom_fichier', site_id),
                            value=value_per_site,
                            key_type=KeyType.STATIC
                        )
                        updated_keys.append(key)
                    
                    self.set_keys(updated_keys, save_history=True)
                    return
                
                # Ajouter les nouveaux sites
                for site_id in added_sites:
                    site_data = new_sites_config[site_id]
                    key = RepartitionKey(
                        site_id=site_id,
                        participant_name=site_data.get('nom_fichier', site_id),
                        value=value_per_new_site,
                        key_type=KeyType.STATIC
                    )
                    updated_keys.append(key)
            
            # Appliquer les clés mises à jour
            self.set_keys(updated_keys, save_history=True)
    
    def _get_default_config(self) -> Dict:
        """Retourne la configuration par défaut"""
        return {
            'mode': 'static',  # static, temporal, rules
            'current_keys': [],
            'temporal_keys': [],
            'rules': [],
            'history': [],
            'last_modified': datetime.now(),
            'validation_status': {'valid': False, 'messages': []},
            'active_template': None,
            'optimization_settings': {
                'objective': 'maximize_self_consumption',  # ou 'minimize_penalties', 'balance_savings'
                'constraints': {}
            }
        }
    
    def _initialize_default_keys(self):
        """Initialise les clés par défaut (répartition équitable)"""
        if not self.sites_config:
            return
        
        # Créer une répartition équitable
        site_count = len(self.sites_config)
        value_per_site = 100.0 / site_count if site_count > 0 else 0
        
        keys = []
        for site_id, site_data in self.sites_config.items():
            key = RepartitionKey(
                site_id=site_id,
                participant_name=site_data.get('nom_fichier', site_id),
                value=value_per_site,
                key_type=KeyType.STATIC
            )
            keys.append(key)
        
        self.set_keys(keys, save_history=False)
        logger.info(f"Clés par défaut initialisées (répartition équitable)")
    
    def get_current_keys(self) -> List[RepartitionKey]:
        """
        Retourne les clés actuellement actives
        
        Returns:
            Liste des clés de répartition
        """
        keys_data = self.config.get('current_keys', [])
        return [RepartitionKey.from_dict(k) for k in keys_data]
    
    def set_keys(self, keys: List[RepartitionKey], validate: bool = True, save_history: bool = True) -> bool:
        """
        Définit les nouvelles clés de répartition
        
        Args:
            keys: Nouvelles clés à appliquer
            validate: Si True, valide les clés avant de les appliquer
            save_history: Si True, sauvegarde l'état actuel dans l'historique
            
        Returns:
            True si les clés ont été appliquées avec succès
        """
        # Validation si demandée
        if validate:
            validation_result = self.validator.validate_complete(
                keys, 
                self.sites_config
            )
            
            if not validation_result['is_valid']:
                logger.warning(f"Validation échouée: {validation_result['errors']}")
                return False
        
        # Sauvegarder dans l'historique si demandé
        if save_history and self.config.get('current_keys'):
            self._save_to_history()
        
        # Appliquer les nouvelles clés
        self.config['current_keys'] = [k.to_dict() for k in keys]
        self.config['last_modified'] = datetime.now()
        
        # Mettre à jour le statut de validation
        if validate:
            self.config['validation_status'] = {
                'valid': validation_result['is_valid'],
                'messages': validation_result['errors'] + validation_result['warnings']
            }
        
        # Sauvegarder dans session_state
        st.session_state.repartition_config = self.config
        
        logger.info(f"Nouvelles clés appliquées: {len(keys)} clés")
        return True
    
    def apply_keys_to_energy_data(self, energy_data: pd.DataFrame, production_column: str = 'Production') -> pd.DataFrame:
        """
        Applique les clés de répartition aux données énergétiques
        
        Args:
            energy_data: DataFrame avec les données de production
            production_column: Nom de la colonne contenant la production totale
            
        Returns:
            DataFrame avec colonnes de production par participant
        """
        if production_column not in energy_data.columns:
            raise ValueError(f"Colonne '{production_column}' non trouvée dans les données")
        
        mode = self.config.get('mode', 'static')
        
        if mode == 'static':
            keys = self.get_current_keys()
            return apply_static_keys(energy_data[production_column], keys)
        
        elif mode == 'temporal':
            temporal_periods = self._get_temporal_periods()
            return apply_temporal_keys(energy_data[production_column], temporal_periods, energy_data.index)
        
        elif mode == 'rules':
            rules = self._get_active_rules()
            consumption_data = self._get_consumption_data(energy_data)
            return apply_dynamic_rules(
                energy_data[production_column], 
                consumption_data, 
                rules
            )
        
        else:
            raise ValueError(f"Mode de répartition non supporté: {mode}")
    
    def validate_keys_coherence(self) -> Tuple[bool, List[str]]:
        """
        Vérifie la cohérence des clés actuelles
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, messages)
        """
        keys = self.get_current_keys()
        validation_result = self.validator.validate_complete(keys, self.sites_config)
        
        messages = validation_result['errors'] + validation_result['warnings']
        return validation_result['is_valid'], messages
    
    def calculate_financial_impact(self, energy_results: Dict, pricing_config: Dict) -> Dict:
        """
        Calcule l'impact financier du changement de clés
        
        Args:
            energy_results: Résultats énergétiques avec répartition
            pricing_config: Configuration des prix
            
        Returns:
            Dict avec l'impact financier par participant
        """
        impact = {}
        
        # Obtenir les clés actuelles
        keys = self.get_current_keys()
        
        for key in keys:
            site_id = key.site_id
            participant_name = key.participant_name
            
            # Calculer les revenus/économies basés sur la répartition
            if site_id in energy_results:
                site_results = energy_results[site_id]
                
                # Production allouée
                allocated_production = site_results.get('allocated_production', 0)
                
                # Prix de vente/autoconsommation
                energy_price = pricing_config.get('energy_price', 0.15)
                
                # Revenus/économies
                financial_value = allocated_production * energy_price
                
                impact[participant_name] = {
                    'allocated_production_kwh': allocated_production,
                    'allocation_percentage': key.value,
                    'financial_value': financial_value,
                    'unit_price': energy_price
                }
        
        # Ajouter les totaux
        total_production = sum(p['allocated_production_kwh'] for p in impact.values())
        total_value = sum(p['financial_value'] for p in impact.values())
        
        impact['_totals'] = {
            'total_production_kwh': total_production,
            'total_financial_value': total_value
        }
        
        return impact
    
    def generate_repartition_report(self) -> Dict:
        """
        Génère un rapport complet de la répartition actuelle
        
        Returns:
            Dict avec les informations de répartition
        """
        keys = self.get_current_keys()
        validation = self.validator.validate_complete(keys, self.sites_config)
        
        report = {
            'timestamp': datetime.now(),
            'mode': self.config.get('mode', 'static'),
            'participants': [],
            'validation': validation,
            'summary': {
                'total_participants': len(keys),
                'total_allocation': sum(k.value for k in keys),
                'is_valid': validation['is_valid']
            }
        }
        
        # Détails par participant
        for key in keys:
            site_config = self.sites_config.get(key.site_id, {})
            participant_info = {
                'site_id': key.site_id,
                'name': key.participant_name,
                'allocation_percentage': key.value,
                'site_type': site_config.get('site_type', 'Producteur'),
                'power_kwc': site_config.get('puissance_kwc', 0),
                'key_type': key.key_type.value
            }
            report['participants'].append(participant_info)
        
        return report
    
    def apply_template(self, template_id: str) -> bool:
        """
        Applique un template prédéfini
        
        Args:
            template_id: ID du template à appliquer
            
        Returns:
            True si le template a été appliqué avec succès
        """
        # Charger le template
        template = self.storage.load_template(template_id)
        if not template:
            logger.error(f"Template '{template_id}' non trouvé")
            return False
        
        # Appliquer le template aux sites
        keys = template.apply_to_sites(self.sites_config)
        
        # Définir les nouvelles clés
        success = self.set_keys(keys, validate=True)
        
        if success:
            self.config['active_template'] = template_id
            logger.info(f"Template '{template_id}' appliqué avec succès")
        
        return success
    
    def optimize_keys(self, objective: str = 'maximize_self_consumption', constraints: Dict = None) -> bool:
        """
        Optimise automatiquement les clés selon un objectif
        
        Args:
            objective: Objectif d'optimisation
            constraints: Contraintes à respecter
            
        Returns:
            True si l'optimisation a réussi
        """
        # Obtenir les données nécessaires
        consumption_data = self._get_historical_consumption()
        production_data = self._get_historical_production()
        
        # Lancer l'optimisation
        optimized_keys = optimize_repartition(
            production_data,
            consumption_data,
            self.sites_config,
            objective=objective,
            constraints=constraints or {}
        )
        
        if optimized_keys:
            # Appliquer les clés optimisées
            return self.set_keys(optimized_keys, validate=True)
        
        return False
    
    def export_to_dict(self) -> Dict:
        """
        Exporte la configuration complète en dictionnaire
        
        Returns:
            Dict avec toute la configuration
        """
        return {
            'version': '1.0',
            'mode': self.config.get('mode'),
            'current_keys': self.config.get('current_keys'),
            'temporal_keys': self.config.get('temporal_keys'),
            'rules': self.config.get('rules'),
            'last_modified': self.config.get('last_modified').isoformat() if self.config.get('last_modified') else None,
            'validation_status': self.config.get('validation_status'),
            'active_template': self.config.get('active_template'),
            'optimization_settings': self.config.get('optimization_settings')
        }
    
    def import_from_dict(self, data: Dict) -> bool:
        """
        Importe une configuration depuis un dictionnaire
        
        Args:
            data: Dictionnaire avec la configuration
            
        Returns:
            True si l'import a réussi
        """
        try:
            # Valider la version
            if data.get('version') != '1.0':
                logger.warning(f"Version non supportée: {data.get('version')}")
            
            # Importer les clés
            if 'current_keys' in data:
                keys = [RepartitionKey.from_dict(k) for k in data['current_keys']]
                self.set_keys(keys, validate=True, save_history=True)
            
            # Importer les autres paramètres
            if 'mode' in data:
                self.config['mode'] = data['mode']
            
            if 'temporal_keys' in data:
                self.config['temporal_keys'] = data['temporal_keys']
            
            if 'rules' in data:
                self.config['rules'] = data['rules']
            
            if 'optimization_settings' in data:
                self.config['optimization_settings'] = data['optimization_settings']
            
            # Sauvegarder
            st.session_state.repartition_config = self.config
            
            logger.info("Configuration importée avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'import: {e}")
            return False
    
    def _save_to_history(self):
        """Sauvegarde l'état actuel dans l'historique"""
        history_entry = {
            'timestamp': datetime.now(),
            'keys': copy.deepcopy(self.config.get('current_keys', [])),
            'mode': self.config.get('mode'),
            'validation_status': copy.deepcopy(self.config.get('validation_status'))
        }
        
        # Limiter l'historique à 10 entrées
        if 'repartition_history' not in st.session_state:
            st.session_state.repartition_history = []
        
        st.session_state.repartition_history.insert(0, history_entry)
        st.session_state.repartition_history = st.session_state.repartition_history[:10]
    
    def restore_from_history(self, index: int) -> bool:
        """
        Restaure une configuration depuis l'historique
        
        Args:
            index: Index dans l'historique (0 = plus récent)
            
        Returns:
            True si la restauration a réussi
        """
        history = st.session_state.get('repartition_history', [])
        
        if 0 <= index < len(history):
            entry = history[index]
            keys = [RepartitionKey.from_dict(k) for k in entry['keys']]
            return self.set_keys(keys, validate=True, save_history=False)
        
        return False
    
    def _get_temporal_periods(self) -> List[RepartitionPeriod]:
        """Retourne les périodes temporelles configurées"""
        periods_data = self.config.get('temporal_keys', [])
        return [RepartitionPeriod.from_dict(p) for p in periods_data]
    
    def _get_active_rules(self) -> List[RepartitionRule]:
        """Retourne les règles actives"""
        rules_data = self.config.get('rules', [])
        rules = [RepartitionRule.from_dict(r) for r in rules_data]
        return [r for r in rules if r.enabled]
    
    def _get_consumption_data(self, energy_data: pd.DataFrame) -> pd.DataFrame:
        """Extrait les données de consommation du DataFrame énergétique"""
        # À adapter selon la structure des données
        consumption_columns = [col for col in energy_data.columns if 'Consommation' in col]
        if consumption_columns:
            return energy_data[consumption_columns]
        return pd.DataFrame()
    
    def _get_historical_consumption(self) -> pd.DataFrame:
        """Retourne les données historiques de consommation"""
        # À implémenter selon la source des données
        if 'sites_data' in st.session_state:
            # Agréger les données de consommation de tous les sites
            pass
        return pd.DataFrame()
    
    def _get_historical_production(self) -> pd.DataFrame:
        """Retourne les données historiques de production"""
        # À implémenter selon la source des données
        if 'energy_data' in st.session_state:
            # Extraire les données de production
            pass
        return pd.DataFrame()