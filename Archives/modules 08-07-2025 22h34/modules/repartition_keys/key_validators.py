"""
Module de validation pour les clés de répartition
"""

from typing import List, Tuple, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from .key_models import RepartitionKey, RepartitionPeriod, RepartitionRule, KeyType


class RepartitionValidator:
    """Classe principale pour la validation des clés de répartition"""
    
    def __init__(self):
        self.tolerance = 0.01  # Tolérance pour la somme à 100%
        self.min_key_value = 0.0
        self.max_key_value = 100.0
    
    def validate_keys_sum(self, keys: List[RepartitionKey]) -> Tuple[bool, str]:
        """
        Vérifie que la somme des clés fait 100%
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        if not keys:
            return False, "Aucune clé de répartition définie"
        
        total = sum(key.value for key in keys)
        
        if abs(total - 100.0) <= self.tolerance:
            return True, f"Somme valide : {total:.2f}%"
        else:
            return False, f"La somme des clés doit faire 100% (actuel: {total:.2f}%)"
    
    def validate_key_values(self, keys: List[RepartitionKey]) -> Tuple[bool, List[str]]:
        """
        Vérifie que toutes les valeurs sont dans les limites acceptables
        
        Returns:
            Tuple[bool, List[str]]: (all_valid, error_messages)
        """
        errors = []
        
        for key in keys:
            if key.value < self.min_key_value:
                errors.append(f"{key.participant_name}: valeur négative ({key.value}%)")
            elif key.value > self.max_key_value:
                errors.append(f"{key.participant_name}: valeur > 100% ({key.value}%)")
            elif key.value == 0:
                errors.append(f"{key.participant_name}: aucune allocation (0%)")
        
        return len(errors) == 0, errors
    
    def validate_site_coverage(self, keys: List[RepartitionKey], sites_config: Dict) -> Tuple[bool, List[str]]:
        """
        Vérifie que tous les sites sont couverts par les clés
        
        Returns:
            Tuple[bool, List[str]]: (all_covered, missing_sites)
        """
        key_sites = {key.site_id for key in keys}
        config_sites = set(sites_config.keys())
        
        missing_sites = config_sites - key_sites
        
        if missing_sites:
            missing_names = [sites_config[site_id].get('nom_fichier', site_id) 
                           for site_id in missing_sites]
            return False, missing_names
        
        return True, []
    
    def validate_temporal_coherence(self, periods: List[RepartitionPeriod]) -> Tuple[bool, List[str]]:
        """
        Vérifie la cohérence temporelle des périodes
        
        Returns:
            Tuple[bool, List[str]]: (is_coherent, issues)
        """
        if not periods:
            return True, []
        
        issues = []
        
        # Trier les périodes par date de début
        sorted_periods = sorted(periods, key=lambda p: p.start_date or datetime.min)
        
        # Vérifier les chevauchements et les trous
        for i in range(len(sorted_periods) - 1):
            current = sorted_periods[i]
            next_period = sorted_periods[i + 1]
            
            if current.end_date and next_period.start_date:
                # Chevauchement
                if current.end_date > next_period.start_date:
                    issues.append(f"Chevauchement entre '{current.period_name}' et '{next_period.period_name}'")
                # Trou
                elif (next_period.start_date - current.end_date).days > 1:
                    gap_days = (next_period.start_date - current.end_date).days - 1
                    issues.append(f"Trou de {gap_days} jours entre '{current.period_name}' et '{next_period.period_name}'")
        
        return len(issues) == 0, issues
    
    def validate_rules_coherence(self, rules: List[RepartitionRule]) -> Tuple[bool, List[str]]:
        """
        Vérifie la cohérence des règles de répartition
        
        Returns:
            Tuple[bool, List[str]]: (is_coherent, issues)
        """
        issues = []
        
        # Vérifier les conflits de priorité
        priority_groups = {}
        for rule in rules:
            if rule.enabled:
                if rule.priority in priority_groups:
                    priority_groups[rule.priority].append(rule)
                else:
                    priority_groups[rule.priority] = [rule]
        
        for priority, rules_group in priority_groups.items():
            if len(rules_group) > 1:
                rule_names = [r.rule_name for r in rules_group]
                issues.append(f"Plusieurs règles avec la même priorité ({priority}): {', '.join(rule_names)}")
        
        # Vérifier les règles contradictoires
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                if self._are_rules_contradictory(rule1, rule2):
                    issues.append(f"Règles potentiellement contradictoires: '{rule1.rule_name}' et '{rule2.rule_name}'")
        
        return len(issues) == 0, issues
    
    def validate_consumption_allocation_ratio(
        self, 
        keys: List[RepartitionKey], 
        consumption_data: Optional[pd.DataFrame] = None,
        threshold: float = 2.0
    ) -> Tuple[bool, List[str]]:
        """
        Vérifie que l'allocation est cohérente avec la consommation historique
        
        Args:
            keys: Liste des clés de répartition
            consumption_data: Données de consommation historique
            threshold: Ratio max acceptable entre allocation et consommation moyenne
            
        Returns:
            Tuple[bool, List[str]]: (is_coherent, warnings)
        """
        if consumption_data is None or consumption_data.empty:
            return True, []
        
        warnings = []
        
        # Calculer la consommation moyenne par site
        site_consumptions = {}
        for site_id in consumption_data.columns:
            if site_id != 'timestamp':
                avg_consumption = consumption_data[site_id].mean()
                site_consumptions[site_id] = avg_consumption
        
        total_consumption = sum(site_consumptions.values())
        
        if total_consumption == 0:
            return True, []
        
        # Vérifier le ratio pour chaque site
        for key in keys:
            if key.site_id in site_consumptions:
                site_consumption = site_consumptions[key.site_id]
                consumption_percentage = (site_consumption / total_consumption) * 100
                
                ratio = key.value / consumption_percentage if consumption_percentage > 0 else float('inf')
                
                if ratio > threshold:
                    warnings.append(
                        f"{key.participant_name}: allocation ({key.value:.1f}%) "
                        f"très supérieure à la consommation moyenne ({consumption_percentage:.1f}%)"
                    )
                elif ratio < 1/threshold:
                    warnings.append(
                        f"{key.participant_name}: allocation ({key.value:.1f}%) "
                        f"très inférieure à la consommation moyenne ({consumption_percentage:.1f}%)"
                    )
        
        return len(warnings) == 0, warnings
    
    def validate_complete(
        self, 
        keys: List[RepartitionKey],
        sites_config: Dict,
        periods: Optional[List[RepartitionPeriod]] = None,
        rules: Optional[List[RepartitionRule]] = None,
        consumption_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, any]:
        """
        Validation complète des clés de répartition
        
        Returns:
            Dict avec les résultats de validation
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        # Validation de la somme
        sum_valid, sum_msg = self.validate_keys_sum(keys)
        results['details']['sum_validation'] = {'valid': sum_valid, 'message': sum_msg}
        if not sum_valid:
            results['errors'].append(sum_msg)
            results['is_valid'] = False
        
        # Validation des valeurs
        values_valid, value_errors = self.validate_key_values(keys)
        results['details']['values_validation'] = {'valid': values_valid, 'errors': value_errors}
        if not values_valid:
            results['errors'].extend(value_errors)
            results['is_valid'] = False
        
        # Validation de la couverture des sites
        coverage_valid, missing_sites = self.validate_site_coverage(keys, sites_config)
        results['details']['coverage_validation'] = {'valid': coverage_valid, 'missing': missing_sites}
        if not coverage_valid:
            results['errors'].append(f"Sites sans allocation: {', '.join(missing_sites)}")
            results['is_valid'] = False
        
        # Validation temporelle si applicable
        if periods:
            temporal_valid, temporal_issues = self.validate_temporal_coherence(periods)
            results['details']['temporal_validation'] = {'valid': temporal_valid, 'issues': temporal_issues}
            if not temporal_valid:
                results['warnings'].extend(temporal_issues)
        
        # Validation des règles si applicable
        if rules:
            rules_valid, rules_issues = self.validate_rules_coherence(rules)
            results['details']['rules_validation'] = {'valid': rules_valid, 'issues': rules_issues}
            if not rules_valid:
                results['warnings'].extend(rules_issues)
        
        # Validation du ratio consommation/allocation
        if consumption_data is not None:
            ratio_valid, ratio_warnings = self.validate_consumption_allocation_ratio(
                keys, consumption_data
            )
            results['details']['consumption_ratio'] = {'valid': ratio_valid, 'warnings': ratio_warnings}
            results['warnings'].extend(ratio_warnings)
        
        return results
    
    def _are_rules_contradictory(self, rule1: RepartitionRule, rule2: RepartitionRule) -> bool:
        """
        Vérifie si deux règles sont potentiellement contradictoires
        """
        if not rule1.enabled or not rule2.enabled:
            return False
        
        # Vérifier si les règles ciblent les mêmes sites
        common_sites = set(rule1.target_sites) & set(rule2.target_sites)
        if not common_sites:
            return False
        
        # Vérifier si les conditions sont contradictoires
        # Implémentation simplifiée - à étendre selon les besoins
        for cond1 in rule1.conditions:
            for cond2 in rule2.conditions:
                if cond1.field == cond2.field:
                    # Vérifier les contradictions évidentes
                    if (cond1.operator == ">" and cond2.operator == "<" and 
                        cond1.value >= cond2.value):
                        return True
                    if (cond1.operator == ">=" and cond2.operator == "<=" and 
                        cond1.value > cond2.value):
                        return True
        
        return False


def quick_validate_keys(keys: List[RepartitionKey]) -> Tuple[bool, str]:
    """
    Validation rapide pour l'interface utilisateur
    
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    validator = RepartitionValidator()
    
    # Vérifier la somme
    sum_valid, sum_msg = validator.validate_keys_sum(keys)
    if not sum_valid:
        return False, sum_msg
    
    # Vérifier les valeurs
    values_valid, value_errors = validator.validate_key_values(keys)
    if not values_valid:
        return False, "; ".join(value_errors[:3])  # Limiter à 3 erreurs
    
    return True, "Clés valides ✓"