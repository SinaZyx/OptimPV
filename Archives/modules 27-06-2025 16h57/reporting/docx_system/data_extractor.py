"""
Extracteur de données OptimPV synchronisé avec le contenu HTML
Utilise exactement les mêmes méthodes que customer_report_commercial.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional


class OptimPVDataExtractor:
    """
    Extracteur de données synchronisé avec le rapport HTML
    Utilise les mêmes méthodes pour garantir un contenu identique
    """
    
    def __init__(self):
        """Initialise l'extracteur de données"""
        self.data = {}
        
    def extract_all_data(self) -> Dict[str, Any]:
        """
        Extrait toutes les données en utilisant les mêmes méthodes que l'HTML
        
        Returns:
            dict: Dictionnaire complet des données formatées IDENTIQUES à l'HTML
        """
        print("🔍 DOCX SYNC EXTRACTOR: Début extraction synchronisée...")
        
        # Import des méthodes depuis customer_report_commercial
        try:
            from ..customer_report_commercial import CommercialCustomerReportModule
            html_module = CommercialCustomerReportModule()
            print("✅ Module HTML importé pour synchronisation")
        except Exception as e:
            print(f"❌ Erreur import module HTML: {e}")
            return self._fallback_extraction()
        
        # Vérifier la disponibilité des données
        if not st.session_state.get('data_imported'):
            print("❌ Aucune donnée importée")
            return {'error': 'Aucune donnée disponible'}
        
        # Utiliser les MÊMES méthodes que l'HTML
        try:
            # 1. Configuration projet (méthode HTML)
            project_config = html_module._get_project_configuration()
            project_totals = html_module._calculate_project_totals(project_config['sites_config'])
            
            # 2. Données d'optimisation (méthode HTML)
            best_scenario, scenario_data, prix_optimal = html_module._get_optimization_data()
            
            # 3. Données énergétiques robustes (méthode HTML)
            energy_data_robust = html_module._get_energy_data_robust()
            
            # 4. Données financières depuis l'engine (méthode HTML)
            financial_data_engine = html_module._get_financial_data_from_engine()
            
            print("✅ Toutes les méthodes HTML exécutées avec succès")
            
        except Exception as e:
            print(f"❌ Erreur méthodes HTML: {e}")
            return self._fallback_extraction()
        
        # Construire les données au format DOCX en utilisant les résultats HTML
        self.data = {
            # === INFORMATIONS GÉNÉRALES ===
            'generated_date': datetime.now().strftime('%d/%m/%Y'),
            'generated_time': datetime.now().strftime('%H:%M'),
            'generated_datetime': datetime.now().strftime('%d/%m/%Y à %H:%M'),
            
            # === PROJET (depuis project_config) ===
            'project_name': project_config['global_config'].get('project_name', 'Projet OptimPV'),
            'client_name': 'Client OptimPV',  # À adapter selon les besoins
            'duree_projet': int(project_config['global_config'].get('duree_ppa', 240) / 12),
            'tarif_edf_reference': project_config['global_config'].get('tarif_edf_reference', 0.20),
            
            # === TOTAUX PROJET (depuis project_totals) ===
            'nombre_sites_producteurs': project_totals.get('nombre_sites_producteurs', 1),
            'nombre_sites_consommateurs': project_totals.get('nombre_sites_consommateurs', 1),
            'puissance_kwc_total': project_totals.get('puissance_kwc_total', 25.0),
            'consommation_annuelle_totale': project_totals.get('consommation_annuelle_totale', 45000),
            
            # === OPTIMISATION (depuis scenario_data) ===
            'prix_optimal': prix_optimal or 0.16,
            'best_scenario': best_scenario or 'Base',
            
            # === ÉNERGÉTIQUE ROBUSTE (depuis energy_data_robust) ===
            'total_consumption': energy_data_robust.get('total_consumption', 45.2),
            'total_autoconsumption': energy_data_robust.get('total_autoconsumption', 18.5),
            'total_grid_purchase': energy_data_robust.get('total_grid_purchase', 26.7),
            'total_production': energy_data_robust.get('total_production', 23.7),
            'total_injection': energy_data_robust.get('total_injection', 5.2),
            
            # === INDICATEURS CLÉS (Section 3.1 HTML) ===
            'autonomy_rate': energy_data_robust.get('autonomy_rate', 40.9),
            'autoconsumption_rate': energy_data_robust.get('autoconsumption_rate', 78.2),
            
            # === FINANCIER (depuis financial_data_engine) ===
            'economie_totale_finale': financial_data_engine.get('economie_totale', 0),
            'economie_annuelle': financial_data_engine.get('economie_annuelle', 0),
            'van_20ans': financial_data_engine.get('van_20ans', 0),
            'tri_percent': financial_data_engine.get('tri_percent', 0),
            
            # === CALCULS COÛTS (Section 3.2 HTML) ===
            # Ces calculs reproduisent exactement la logique HTML
            'cout_sans_pv': self._calculate_cout_sans_pv(energy_data_robust, project_config),
            'cout_avec_pv_total': self._calculate_cout_avec_pv_total(energy_data_robust, project_config, prix_optimal),
            'cout_avec_pv_solaire': self._calculate_cout_avec_pv_solaire(energy_data_robust, prix_optimal),
            'cout_avec_pv_reseau': self._calculate_cout_avec_pv_reseau(energy_data_robust, project_config),
            'economie_annuelle_calculee': 0,  # Sera calculé après
            
            # === AVANTAGE CUMULÉ (Section 3.3 HTML) ===
            'taux_inflation': project_config['global_config'].get('taux_inflation', 0.02),
            'economies_cumulees_20ans': 0,  # Sera calculé
            
            # === DONNÉES BRUTES POUR DOCX ===
            '_project_config': project_config,
            '_project_totals': project_totals,
            '_scenario_data': scenario_data,
            '_energy_data_robust': energy_data_robust,
            '_financial_data_engine': financial_data_engine
        }
        
        # Calculs dérivés (comme dans l'HTML)
        self.data['economie_annuelle_calculee'] = self.data['cout_sans_pv'] - self.data['cout_avec_pv_total']
        self.data['economies_cumulees_20ans'] = self.data['economie_annuelle_calculee'] * self.data['duree_projet']
        self.data['pourcentage_economie'] = (self.data['economie_annuelle_calculee'] / self.data['cout_sans_pv'] * 100) if self.data['cout_sans_pv'] > 0 else 0
        
        print(f"✅ DOCX SYNC EXTRACTOR: {len(self.data)} variables extraites (synchronisées avec HTML)")
        return self.data
    
    def _calculate_cout_sans_pv(self, energy_data_robust, project_config):
        """Calcule le coût sans PV (même logique que HTML)"""
        tarif_edf = project_config['global_config'].get('tarif_edf_reference', 0.20)
        return energy_data_robust['total_consumption'] * tarif_edf * 1000  # MWh vers kWh
    
    def _calculate_cout_avec_pv_total(self, energy_data_robust, project_config, prix_optimal):
        """Calcule le coût total avec PV (même logique que HTML)"""
        cout_solaire = self._calculate_cout_avec_pv_solaire(energy_data_robust, prix_optimal)
        cout_reseau = self._calculate_cout_avec_pv_reseau(energy_data_robust, project_config)
        return cout_solaire + cout_reseau
    
    def _calculate_cout_avec_pv_solaire(self, energy_data_robust, prix_optimal):
        """Calcule le coût de l'énergie solaire (même logique que HTML)"""
        prix_optimal = prix_optimal or 0.16
        return energy_data_robust['total_autoconsumption'] * prix_optimal * 1000  # MWh vers kWh
    
    def _calculate_cout_avec_pv_reseau(self, energy_data_robust, project_config):
        """Calcule le coût de l'énergie réseau restante (même logique que HTML)"""
        tarif_edf = project_config['global_config'].get('tarif_edf_reference', 0.20)
        return energy_data_robust['total_grid_purchase'] * tarif_edf * 1000  # MWh vers kWh
    
    def _fallback_extraction(self) -> Dict[str, Any]:
        """Extraction de fallback si les méthodes HTML ne marchent pas"""
        print("⚠️ Mode fallback activé")
        
        # Données minimales pour éviter les erreurs DOCX
        return {
            'generated_date': datetime.now().strftime('%d/%m/%Y'),
            'generated_datetime': datetime.now().strftime('%d/%m/%Y à %H:%M'),
            'project_name': st.session_state.get('config', {}).get('project_name', 'Projet OptimPV'),
            'client_name': 'Client OptimPV',
            'puissance_kwc_total': 25.0,
            'prix_optimal': 0.16,
            'autonomy_rate': 40.0,
            'autoconsumption_rate': 75.0,
            'economie_totale_finale': 8500,
            'duree_projet': 20,
            'cout_sans_pv': 9000,
            'cout_avec_pv_total': 6500,
            'economie_annuelle_calculee': 2500,
            'economies_cumulees_20ans': 50000,
            'pourcentage_economie': 27.8,
            '_fallback_mode': True
        }
    
    def format_currency(self, amount, decimals=0):
        """Formatage monétaire (comme dans l'HTML)"""
        if decimals == 0:
            return f"{amount:,.0f} €".replace(',', ' ')
        else:
            return f"{amount:,.{decimals}f} €".replace(',', ' ')
    
    def format_percentage(self, rate, decimals=1):
        """Formatage pourcentage (comme dans l'HTML)"""
        return f"{rate:.{decimals}f}%"
    
    def format_number(self, number, decimals=0, unit=''):
        """Formatage nombre (comme dans l'HTML)"""
        formatted = f"{number:,.{decimals}f}".replace(',', ' ')
        return f"{formatted} {unit}".strip()