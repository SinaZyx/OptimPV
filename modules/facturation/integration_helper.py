"""
Module d'intégration pour connecter la facturation aux autres modules OptimPV
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class OptimPVIntegration:
    """Classe pour intégrer la facturation avec les modules existants d'OptimPV"""
    
    @staticmethod
    def get_project_from_config() -> Dict[str, Any]:
        """Récupère les données du projet depuis ConfigModule"""
        # Vérifier si la configuration globale existe
        if 'config' not in st.session_state:
            logger.warning("Configuration globale non trouvée dans session_state")
            return {}
        
        config = st.session_state.config
        
        # Récupérer les paramètres du projet depuis la config globale
        project_data = {
            'name': config.get('project_name', 'Projet OptimPV'),
            'client_name': config.get('nom_porteur_projet', 'Client OptimPV'),
            'address': config.get('project_address', 'France'),
            'start_date': date.today(),
            'end_date': date.today().replace(year=date.today().year + config.get('analyse_duration_years', 20)),
            'total_capacity_kwc': 0.0,  # Sera calculé depuis les sites
            'total_investment': 0.0,    # Sera calculé depuis les sites
            'financing_percentage': config.get('debt_ratio', 0.80) * 100,
            'annual_production_kwh': 0.0  # Sera calculé depuis les sites
        }
        
        # Récupérer les données des sites pour calculer les totaux
        if 'sites_config' in st.session_state and st.session_state.sites_config:
            total_capacity = 0.0
            total_capex = 0.0
            total_production = 0.0
            
            for site_id, site_data in st.session_state.sites_config.items():
                # Puissance
                site_capacity = site_data.get('puissance_kwc', 0.0)
                total_capacity += site_capacity
                
                # CAPEX
                site_capex = site_data.get('capex_total_eur', site_capacity * 1500)  # Estimation si manquant
                total_capex += site_capex
                
                # Production annuelle
                site_production = site_data.get('production_annuelle_kwh', site_capacity * 1200)  # Estimation si manquant
                total_production += site_production
            
            project_data['total_capacity_kwc'] = total_capacity
            project_data['total_investment'] = total_capex
            project_data['annual_production_kwh'] = total_production
        
        return project_data
    
    @staticmethod
    def get_participants_from_repartition_keys() -> List[Dict[str, Any]]:
        """Récupère les participants depuis le module de répartition des clés"""
        participants = []
        
        # Vérifier si le module de répartition existe
        try:
            from modules.repartition_keys.key_manager import RepartitionKeyManager
            
            # Si un manager existe dans la session
            if 'repartition_manager' in st.session_state:
                manager = st.session_state.repartition_manager
                keys = manager.get_current_keys()
                
                for key in keys:
                    site_config = manager.sites_config.get(key.site_id, {})
                    participant = {
                        'name': key.participant_name,
                        'type': 'consumer' if site_config.get('site_type') == 'Consommateur' else 'producer',
                        'allocation_percentage': key.value,
                        'annual_consumption_kwh': site_config.get('consommation_annuelle_kwh', 3000.0),
                        'address': site_config.get('adresse', ''),
                        'contact_email': site_config.get('email', ''),
                        'consumption_profile_id': key.site_id
                    }
                    participants.append(participant)
                    
        except ImportError:
            logger.info("Module repartition_keys non disponible, utilisation des données par défaut")
            
        # Si pas de participants, créer des participants par défaut
        if not participants:
            participants = [
                {
                    'name': 'Producteur Principal',
                    'type': 'producer',
                    'allocation_percentage': 60.0,
                    'annual_consumption_kwh': 0.0,
                    'address': 'Site de production'
                },
                {
                    'name': 'Consommateur A',
                    'type': 'consumer',
                    'allocation_percentage': 25.0,
                    'annual_consumption_kwh': 3500.0,
                    'address': 'Bâtiment A'
                },
                {
                    'name': 'Consommateur B',
                    'type': 'consumer',
                    'allocation_percentage': 15.0,
                    'annual_consumption_kwh': 2000.0,
                    'address': 'Bâtiment B'
                }
            ]
        
        return participants
    
    @staticmethod
    def get_production_consumption_data() -> Dict[str, pd.DataFrame]:
        """Récupère les données de production et consommation depuis DataImportModule"""
        data = {
            'production': pd.DataFrame(),
            'consumption': pd.DataFrame()
        }
        
        if 'data_import_module' not in st.session_state:
            logger.warning("DataImportModule non trouvé dans session_state")
            return data
        
        import_module = st.session_state.data_import_module
        
        # Récupérer les données de production
        if hasattr(import_module, 'production_data') and import_module.production_data is not None:
            data['production'] = import_module.production_data
        elif 'production_data' in st.session_state and st.session_state.production_data is not None:
            data['production'] = st.session_state.production_data
        
        # Récupérer les données de consommation
        if hasattr(import_module, 'consumption_data') and import_module.consumption_data is not None:
            data['consumption'] = import_module.consumption_data
        elif 'consumption_data' in st.session_state and st.session_state.consumption_data is not None:
            data['consumption'] = st.session_state.consumption_data
        
        # Si pas de données, créer des données de test
        if data['production'].empty:
            logger.info("Génération de données de production de test")
            months = pd.date_range(start='2024-01-01', periods=12, freq='M')
            production_values = np.array([6000, 7000, 8500, 9500, 11000, 12000, 
                                        12500, 11500, 9000, 7500, 6500, 5500])
            data['production'] = pd.DataFrame({
                'date': months,
                'production_kwh': production_values,
                'autoconsommation_kwh': production_values * 0.75,
                'injection_kwh': production_values * 0.25
            })
        
        if data['consumption'].empty:
            logger.info("Génération de données de consommation de test")
            # Créer des données pour 3 consommateurs
            months = pd.date_range(start='2024-01-01', periods=12, freq='M')
            consumption_data = []
            
            for i, consumer in enumerate(['Consommateur A', 'Consommateur B', 'Consommateur C']):
                base_consumption = [250, 240, 220, 200, 180, 170, 190, 200, 210, 230, 240, 260]
                consumption_values = np.array(base_consumption) * (1 + i * 0.2)  # Variation par consommateur
                
                for j, month in enumerate(months):
                    consumption_data.append({
                        'date': month,
                        'participant': consumer,
                        'consumption_kwh': consumption_values[j],
                        'autoconsommation_kwh': consumption_values[j] * 0.6,
                        'grid_consumption_kwh': consumption_values[j] * 0.4
                    })
            
            data['consumption'] = pd.DataFrame(consumption_data)
        
        return data
    
    @staticmethod
    def get_optimal_price() -> float:
        """Récupère le prix optimal depuis les résultats d'analyse"""
        # Prix par défaut
        default_price = 0.15
        
        # Chercher dans les résultats d'optimisation
        if 'optimization_results' in st.session_state and st.session_state.optimization_results:
            opt_results = st.session_state.optimization_results
            if 'prix_optimal_eur_kwh' in opt_results:
                return opt_results['prix_optimal_eur_kwh']
            elif 'best_price' in opt_results:
                return opt_results['best_price']
        
        # Chercher dans les résultats économiques
        if 'economic_results' in st.session_state and st.session_state.economic_results:
            eco_results = st.session_state.economic_results
            if 'prix_vente_eur_kwh' in eco_results:
                return eco_results['prix_vente_eur_kwh']
        
        # Chercher dans la configuration globale
        if 'config' in st.session_state:
            config = st.session_state.config
            if 'prix_vente_electricite_eur_kwh' in config:
                return config['prix_vente_electricite_eur_kwh']
        
        logger.info(f"Prix optimal non trouvé, utilisation du prix par défaut: {default_price} €/kWh")
        return default_price
    
    @staticmethod
    def sync_with_storage(billing_db) -> bool:
        """Synchronise la base de données de facturation avec StorageModule"""
        try:
            if 'storage_module' not in st.session_state:
                logger.warning("StorageModule non trouvé")
                return False
            
            storage = st.session_state.storage_module
            
            # Sauvegarder les paramètres de facturation dans le storage
            billing_settings = {
                'autoconsumption_price': billing_db.get_setting('autoconsumption_price_eur_kwh'),
                'tax_rate': billing_db.get_setting('tax_rate'),
                'invoice_prefix': billing_db.get_setting('invoice_prefix'),
                'payment_terms_days': billing_db.get_setting('default_payment_terms_days')
            }
            
            # Ajouter aux métadonnées du projet
            if hasattr(storage, 'save_metadata'):
                storage.save_metadata('billing_settings', billing_settings)
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation avec StorageModule: {e}")
            
        return False
    
    @staticmethod
    def calculate_monthly_billing_from_data(production_df: pd.DataFrame, 
                                          consumption_df: pd.DataFrame,
                                          participants: List[Dict],
                                          year: int, 
                                          month: int) -> List[Dict[str, Any]]:
        """Calcule la facturation mensuelle à partir des données existantes"""
        billing_data = []
        
        # Filtrer les données pour le mois spécifié
        if not production_df.empty:
            prod_month = production_df[
                (pd.to_datetime(production_df['date']).dt.year == year) & 
                (pd.to_datetime(production_df['date']).dt.month == month)
            ]
            
            if not prod_month.empty:
                total_autoconso = prod_month['autoconsommation_kwh'].iloc[0]
            else:
                # Estimation si pas de données
                total_autoconso = 8000 / 12  # Production annuelle / 12 mois
        else:
            total_autoconso = 8000 / 12
        
        # Répartir selon les allocations
        for participant in participants:
            if participant['type'] == 'consumer':
                participant_autoconso = total_autoconso * (participant['allocation_percentage'] / 100)
                
                billing_data.append({
                    'participant_name': participant['name'],
                    'autoconsumption_kwh': participant_autoconso,
                    'allocation_percentage': participant['allocation_percentage']
                })
        
        return billing_data
    
    @staticmethod
    def get_company_info_from_config() -> Dict[str, str]:
        """Récupère les informations de la société depuis la configuration"""
        company_info = {
            'company_name': 'OptimPV',
            'company_address': '',
            'company_siret': ''
        }
        
        # Récupérer depuis la configuration globale
        if 'config' in st.session_state:
            config = st.session_state.config
            company_info['company_name'] = config.get('nom_porteur_projet', 'OptimPV')
            company_info['company_address'] = config.get('company_address', '')
            company_info['company_siret'] = config.get('company_siret', '')
        
        return company_info