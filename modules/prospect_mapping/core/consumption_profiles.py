#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de profils de consommation horaires pour OptimPV
Basé sur les données ADEME/RTE pour la France
"""

import logging
import os
import time
import json
from typing import Dict, List, Optional

# Import conditionnel de numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Import conditionnel pour téléchargement
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class RealConsumptionProfiles:
    """Télécharge et gère les vrais profils Enedis officiels"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.cache_duration = 86400 * 30  # 30 jours
        
        # Mapping types utilisateur -> profils Enedis
        self.profile_mapping = {
            'residential_family': 'RES1',     # Résidentiel standard
            'residential_telework': 'RES11',  # Résidentiel chauffage élec
            'office': 'PRO1',                 # Professionnel standard  
            'retail': 'PRO2',                 # Professionnel chauffage
            'industrial_2x8': 'ENT',          # Entreprise
            'industrial_3x8': 'ENT'           # Entreprise
        }
        
        # URLs des profils Enedis (format fictif - à adapter selon vraie URL)
        self.enedis_urls = {
            'RES1': 'https://www.enedis.fr/sites/default/files/profil_RES1_2024.csv',
            'RES11': 'https://www.enedis.fr/sites/default/files/profil_RES11_2024.csv',
            'PRO1': 'https://www.enedis.fr/sites/default/files/profil_PRO1_2024.csv',
            'PRO2': 'https://www.enedis.fr/sites/default/files/profil_PRO2_2024.csv',
            'ENT': 'https://www.enedis.fr/sites/default/files/profil_ENT_2024.csv'
        }
        
        # Créer dossier cache
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_enedis_profile(self, user_type: str) -> Optional[List[float]]:
        """
        Récupère le profil Enedis pour un type utilisateur
        
        Args:
            user_type: Type de bâtiment utilisateur
            
        Returns:
            Liste de 8760 valeurs horaires ou None si échec
        """
        try:
            # Mapper vers profil Enedis
            enedis_code = self.profile_mapping.get(user_type)
            if not enedis_code:
                logger.warning(f"Type {user_type} non mappé vers Enedis")
                return None
            
            # Vérifier cache
            cache_file = os.path.join(self.cache_dir, f"enedis_{enedis_code}.json")
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Vérifier fraîcheur
                if time.time() - cache_data['timestamp'] < self.cache_duration:
                    logger.info(f"Cache Enedis {enedis_code} utilisé")
                    return cache_data['profile']
            
            # Télécharger profil
            if REQUESTS_AVAILABLE:
                profile = self._download_enedis_profile(enedis_code)
                if profile:
                    # Sauver en cache
                    cache_data = {
                        'timestamp': time.time(),
                        'profile': profile,
                        'source': f'enedis_{enedis_code}'
                    }
                    with open(cache_file, 'w') as f:
                        json.dump(cache_data, f)
                    
                    return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération profil Enedis {user_type}: {e}")
            return None
    
    def _download_enedis_profile(self, enedis_code: str) -> Optional[List[float]]:
        """Télécharge un profil depuis Enedis"""
        try:
            url = self.enedis_urls.get(enedis_code)
            if not url:
                return None
            
            logger.info(f"Téléchargement profil Enedis {enedis_code}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Parser le CSV Enedis
                # Format attendu : une valeur par ligne, 8760 lignes
                lines = response.text.strip().split('\n')
                
                # Ignorer header si présent
                if 'heure' in lines[0].lower() or 'profil' in lines[0].lower():
                    lines = lines[1:]
                
                # Extraire les valeurs
                profile = []
                for line in lines[:8760]:  # Assurer 8760 max
                    try:
                        # Supposer format CSV simple ou valeur seule
                        value = float(line.split(',')[-1].strip())
                        profile.append(max(0, value))  # Assurer valeurs positives
                    except (ValueError, IndexError):
                        continue
                
                # Vérifier qu'on a bien 8760 valeurs
                if len(profile) == 8760:
                    logger.info(f"Profil Enedis {enedis_code} téléchargé : {len(profile)} valeurs")
                    return profile
                else:
                    logger.warning(f"Profil Enedis {enedis_code} incomplet : {len(profile)}/8760 valeurs")
                    return None
            
            else:
                logger.warning(f"Échec téléchargement Enedis {enedis_code}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur téléchargement Enedis {enedis_code}: {e}")
            return None

class ConsumptionProfileManager:
    """Gestionnaire de profils de consommation horaires"""
    
    def __init__(self):
        # Gestionnaire des vrais profils Enedis
        self.real_profiles = RealConsumptionProfiles()
        
        # Profils de base normalisés (somme = 24) - FALLBACK
        # Source : études ADEME sectorielles
        self.base_profiles = {
            'residential_family': {
                'summer_weekday': [
                    0.5, 0.4, 0.3, 0.3, 0.3, 0.5, 0.8, 1.0,  # 00h-07h
                    0.7, 0.5, 0.4, 0.4, 0.5, 0.5, 0.5, 0.6,  # 08h-15h
                    0.7, 0.9, 1.2, 1.5, 1.4, 1.2, 0.9, 0.7   # 16h-23h
                ],
                'winter_weekday': [
                    0.6, 0.5, 0.4, 0.4, 0.4, 0.6, 1.0, 1.2,  # Plus de chauffage matin
                    0.8, 0.6, 0.5, 0.5, 0.6, 0.6, 0.6, 0.8,
                    1.0, 1.3, 1.6, 1.8, 1.7, 1.5, 1.2, 0.9   # Pic plus important
                ],
                'weekend_factor': 1.1  # 10% de plus le weekend
            },
            'residential_telework': {
                'summer_weekday': [
                    0.5, 0.4, 0.3, 0.3, 0.3, 0.5, 0.8, 1.0,
                    0.9, 0.8, 0.8, 0.9, 1.0, 0.9, 0.8, 0.8,  # Conso jour
                    0.9, 1.0, 1.2, 1.3, 1.2, 1.0, 0.8, 0.6
                ],
                'winter_weekday': [
                    0.6, 0.5, 0.4, 0.4, 0.4, 0.6, 1.0, 1.2,
                    1.0, 0.9, 0.9, 1.0, 1.1, 1.0, 0.9, 0.9,
                    1.1, 1.3, 1.5, 1.6, 1.5, 1.3, 1.0, 0.8
                ],
                'weekend_factor': 1.05
            },
            'office': {
                'summer_weekday': [
                    0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.4, 0.8,  # 00h-07h
                    1.2, 1.4, 1.4, 1.4, 1.2, 1.4, 1.4, 1.4,  # 08h-15h plein régime
                    1.3, 1.0, 0.6, 0.3, 0.2, 0.2, 0.2, 0.2   # 16h-23h
                ],
                'winter_weekday': [
                    0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.5, 1.0,
                    1.4, 1.6, 1.6, 1.6, 1.4, 1.6, 1.6, 1.6,
                    1.5, 1.2, 0.8, 0.4, 0.3, 0.3, 0.3, 0.3
                ],
                'weekend_factor': 0.1  # 90% de réduction weekend
            },
            'retail': {
                'summer_weekday': [
                    0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.5,  # 00h-07h
                    0.8, 1.2, 1.4, 1.5, 1.5, 1.5, 1.5, 1.5,  # 08h-15h
                    1.5, 1.5, 1.4, 1.2, 0.8, 0.4, 0.2, 0.1   # 16h-23h
                ],
                'winter_weekday': [
                    0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.3, 0.6,
                    1.0, 1.4, 1.6, 1.7, 1.7, 1.7, 1.7, 1.7,
                    1.7, 1.7, 1.6, 1.4, 1.0, 0.5, 0.3, 0.2
                ],
                'weekend_factor': 0.9  # Ouvert le samedi
            },
            'industrial_2x8': {
                'summer_weekday': [
                    0.3, 0.3, 0.3, 0.3, 0.3, 0.5, 1.5, 1.5,  # 00h-07h (équipe matin)
                    1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5,  # 08h-15h
                    1.5, 1.5, 1.5, 1.5, 1.5, 1.5, 0.5, 0.3   # 16h-23h (équipe soir)
                ],
                'winter_weekday': [
                    0.4, 0.4, 0.4, 0.4, 0.4, 0.6, 1.7, 1.7,
                    1.7, 1.7, 1.7, 1.7, 1.7, 1.7, 1.7, 1.7,
                    1.7, 1.7, 1.7, 1.7, 1.7, 1.7, 0.6, 0.4
                ],
                'weekend_factor': 0.3  # Production réduite weekend
            },
            'industrial_3x8': {
                'summer_weekday': [
                    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,  # Production 24/24
                    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
                ],
                'winter_weekday': [
                    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                    1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0
                ],
                'weekend_factor': 1.0  # Production continue
            }
        }
        
        # Facteurs saisonniers par type
        self.seasonal_factors = {
            'residential_family': {'summer': 0.85, 'winter': 1.15},
            'residential_telework': {'summer': 0.87, 'winter': 1.13},
            'office': {'summer': 0.90, 'winter': 1.10},
            'retail': {'summer': 0.92, 'winter': 1.08},
            'industrial_2x8': {'summer': 0.95, 'winter': 1.05},
            'industrial_3x8': {'summer': 0.98, 'winter': 1.02}
        }
    
    def create_custom_profile(self, base_profile: str, adjustments: dict) -> dict:
        """
        Crée un profil personnalisé à partir d'un profil de base
        
        Args:
            base_profile: Type de profil de base
            adjustments: Dict avec les ajustements:
                - morning_shift: Décalage pic matin (heures)
                - evening_shift: Décalage pic soir (heures)
                - day_factor: Facteur consommation jour
        """
        if base_profile not in self.base_profiles:
            logger.warning(f"Profil {base_profile} inconnu, utilisation residential_family")
            base_profile = 'residential_family'
        
        custom_profile = self.base_profiles[base_profile].copy()
        
        # Appliquer les ajustements
        if adjustments:
            for season in ['summer_weekday', 'winter_weekday']:
                original = custom_profile[season]
                adjusted = original.copy()
                
                # Décalage pic matin
                if 'morning_shift' in adjustments and adjustments['morning_shift'] != 0:
                    shift = int(adjustments['morning_shift'])
                    # Identifier le pic matin (généralement entre 6h et 10h)
                    if NUMPY_AVAILABLE:
                        morning_peak_idx = np.argmax(original[6:11]) + 6
                    else:
                        morning_peak_idx = original[6:11].index(max(original[6:11])) + 6
                    adjusted = self._shift_peak(adjusted, morning_peak_idx, shift)
                
                # Décalage pic soir
                if 'evening_shift' in adjustments and adjustments['evening_shift'] != 0:
                    shift = int(adjustments['evening_shift'])
                    # Identifier le pic soir (généralement entre 17h et 21h)
                    if NUMPY_AVAILABLE:
                        evening_peak_idx = np.argmax(original[17:22]) + 17
                    else:
                        evening_peak_idx = original[17:22].index(max(original[17:22])) + 17
                    adjusted = self._shift_peak(adjusted, evening_peak_idx, shift)
                
                # Facteur jour
                if 'day_factor' in adjustments:
                    factor = adjustments['day_factor']
                    # Appliquer le facteur entre 8h et 18h
                    for h in range(8, 18):
                        adjusted[h] *= factor
                
                custom_profile[season] = adjusted
        
        return custom_profile
    
    def _shift_peak(self, profile: list, peak_idx: int, shift: int) -> list:
        """Décale un pic dans le profil"""
        shifted = profile.copy()
        if 0 <= peak_idx + shift < 24:
            # Décaler les valeurs autour du pic
            for i in range(max(0, peak_idx - 2), min(24, peak_idx + 3)):
                new_idx = i + shift
                if 0 <= new_idx < 24:
                    shifted[new_idx] = profile[i]
        return shifted
    
    def get_8760_profile(self, annual_kwh: float, profile_type: str, 
                        custom_adjustments: dict = None) -> list:
        """
        Génère 8760 valeurs horaires (année complète)
        
        Args:
            annual_kwh: Consommation annuelle totale
            profile_type: Type de bâtiment
            custom_adjustments: Ajustements personnalisés
            
        Returns:
            List de 8760 valeurs horaires en kW
        """
        
        # 1. Essayer d'abord les vrais profils Enedis (si pas d'ajustements custom)
        if not custom_adjustments:
            real_profile = self.real_profiles.get_enedis_profile(profile_type)
            if real_profile:
                logger.info(f"Utilisation profil Enedis réel pour {profile_type}")
                # Normaliser le profil réel à la consommation demandée
                total_real = sum(real_profile)
                if total_real > 0:
                    return [(value * annual_kwh / total_real) for value in real_profile]
        
        # 2. Fallback sur profils synthétiques
        logger.info(f"Utilisation profil synthétique pour {profile_type}")
        
        # Utiliser profil personnalisé si ajustements fournis
        if custom_adjustments:
            profile_data = self.create_custom_profile(profile_type, custom_adjustments)
        else:
            profile_data = self.base_profiles.get(profile_type, self.base_profiles['residential_family'])
        
        hourly_values = []
        
        # Générer pour chaque jour de l'année
        for day in range(365):
            # Déterminer si weekend et saison
            is_weekend = (day % 7) in [5, 6]
            is_summer = 90 <= day <= 270  # Approximation avril-septembre
            
            # Sélectionner le profil journalier
            if is_summer:
                daily_profile = profile_data['summer_weekday']
            else:
                daily_profile = profile_data['winter_weekday']
            
            # Appliquer facteur weekend
            if is_weekend:
                factor = profile_data['weekend_factor']
                daily_profile = [h * factor for h in daily_profile]
            
            # Appliquer facteur saisonnier
            season = 'summer' if is_summer else 'winter'
            seasonal_factor = self.seasonal_factors[profile_type][season]
            daily_profile = [h * seasonal_factor for h in daily_profile]
            
            # Normaliser pour que la somme = consommation journalière
            daily_kwh = annual_kwh / 365
            profile_sum = sum(daily_profile)
            normalized = [h * daily_kwh / profile_sum for h in daily_profile]
            
            # Convertir en kW (valeurs horaires)
            hourly_kw = [kwh for kwh in normalized]
            hourly_values.extend(hourly_kw)
        
        return hourly_values
    
    def get_profile_stats(self, profile_type: str) -> dict:
        """Retourne des statistiques sur un profil"""
        if profile_type not in self.base_profiles:
            return {}
        
        profile = self.base_profiles[profile_type]
        summer = profile['summer_weekday']
        winter = profile['winter_weekday']
        
        return {
            'summer_peak_hour': summer.index(max(summer)),
            'winter_peak_hour': winter.index(max(winter)),
            'summer_min_hour': summer.index(min(summer)),
            'winter_min_hour': winter.index(min(winter)),
            'day_night_ratio_summer': sum(summer[8:20]) / sum(summer[20:] + summer[:8]),
            'day_night_ratio_winter': sum(winter[8:20]) / sum(winter[20:] + winter[:8]),
            'weekend_factor': profile['weekend_factor']
        }
    
    def get_profile_source(self, profile_type: str) -> str:
        """Retourne la source du profil utilisé"""
        real_profile = self.real_profiles.get_enedis_profile(profile_type)
        if real_profile:
            enedis_code = self.real_profiles.profile_mapping.get(profile_type, 'UNKNOWN')
            return f"Enedis {enedis_code} (données réelles)"
        else:
            return "Profil synthétique ADEME"