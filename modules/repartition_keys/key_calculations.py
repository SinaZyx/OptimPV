"""
Module de calcul pour l'application des clés de répartition
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

from .key_models import RepartitionKey, RepartitionPeriod, RepartitionRule, RuleType

logger = logging.getLogger(__name__)


def apply_static_keys(production: pd.Series, keys: List[RepartitionKey]) -> pd.DataFrame:
    """
    Applique des clés fixes à la production
    
    Args:
        production: Série pandas avec la production totale
        keys: Liste des clés de répartition statiques
        
    Returns:
        DataFrame avec colonnes par participant
    """
    if production.empty or not keys:
        return pd.DataFrame(index=production.index)
    
    # Créer le DataFrame résultat
    result = pd.DataFrame(index=production.index)
    
    # Appliquer chaque clé
    for key in keys:
        column_name = f"Production_{key.participant_name}"
        # Calculer la production allouée
        result[column_name] = production * (key.value / 100.0)
    
    # Ajouter une colonne de vérification
    result['_Total_Allocated'] = result.sum(axis=1)
    result['_Difference'] = production - result['_Total_Allocated']
    
    # Vérifier que la somme est correcte (avec tolérance)
    max_diff = result['_Difference'].abs().max()
    if max_diff > 0.01:
        logger.warning(f"Différence maximale dans l'allocation: {max_diff}")
    
    return result


def apply_temporal_keys(
    production: pd.Series, 
    temporal_periods: List[RepartitionPeriod],
    time_index: pd.DatetimeIndex
) -> pd.DataFrame:
    """
    Applique des clés qui varient dans le temps
    
    Args:
        production: Série pandas avec la production totale
        temporal_periods: Liste des périodes avec leurs clés
        time_index: Index temporel pour déterminer quelle période appliquer
        
    Returns:
        DataFrame avec colonnes par participant
    """
    if production.empty or not temporal_periods:
        return pd.DataFrame(index=production.index)
    
    # Trier les périodes par date de début
    sorted_periods = sorted(
        temporal_periods, 
        key=lambda p: p.start_date if p.start_date else datetime.min
    )
    
    # Créer le DataFrame résultat
    result = pd.DataFrame(index=production.index)
    
    # Obtenir tous les participants uniques
    all_participants = set()
    for period in temporal_periods:
        for key in period.keys:
            all_participants.add(key.participant_name)
    
    # Initialiser les colonnes
    for participant in all_participants:
        result[f"Production_{participant}"] = 0.0
    
    # Appliquer les clés période par période
    for timestamp, prod_value in production.items():
        # Trouver la période applicable
        applicable_period = None
        
        for period in sorted_periods:
            if period.start_date and period.end_date:
                if period.start_date <= timestamp <= period.end_date:
                    applicable_period = period
                    break
            elif period.start_date:
                if timestamp >= period.start_date:
                    applicable_period = period
        
        # Appliquer les clés de la période
        if applicable_period:
            for key in applicable_period.keys:
                column_name = f"Production_{key.participant_name}"
                if column_name in result.columns:
                    result.loc[timestamp, column_name] = prod_value * (key.value / 100.0)
    
    # Ajouter les colonnes de vérification
    result['_Total_Allocated'] = result[[c for c in result.columns if c.startswith('Production_')]].sum(axis=1)
    result['_Difference'] = production - result['_Total_Allocated']
    
    return result


def apply_dynamic_rules(
    production: pd.Series, 
    consumption: pd.DataFrame,
    rules: List[RepartitionRule]
) -> pd.DataFrame:
    """
    Applique des règles dynamiques complexes
    
    Args:
        production: Série pandas avec la production totale
        consumption: DataFrame avec la consommation par site
        rules: Liste des règles de répartition
        
    Returns:
        DataFrame avec colonnes par participant
    """
    if production.empty:
        return pd.DataFrame(index=production.index)
    
    # Trier les règles par priorité (décroissante)
    sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)
    
    # Créer le DataFrame résultat
    result = pd.DataFrame(index=production.index)
    
    # Pour chaque timestamp
    for timestamp, prod_value in production.items():
        # Contexte pour l'évaluation des règles
        context = {
            'timestamp': timestamp,
            'production': prod_value,
            'hour': timestamp.hour if hasattr(timestamp, 'hour') else 0,
            'month': timestamp.month if hasattr(timestamp, 'month') else 1,
            'weekday': timestamp.weekday() if hasattr(timestamp, 'weekday') else 0
        }
        
        # Ajouter les données de consommation au contexte
        if not consumption.empty and timestamp in consumption.index:
            for col in consumption.columns:
                context[f'consumption_{col}'] = consumption.loc[timestamp, col]
        
        # Production restante à allouer
        remaining_production = prod_value
        allocations = {}
        
        # Appliquer les règles dans l'ordre de priorité
        for rule in sorted_rules:
            if remaining_production <= 0:
                break
            
            if rule.applies_to_context(context):
                # Appliquer la règle selon son type
                if rule.rule_type == RuleType.PRIORITY:
                    allocation = _apply_priority_rule(
                        rule, remaining_production, context, consumption, timestamp
                    )
                elif rule.rule_type == RuleType.THRESHOLD:
                    allocation = _apply_threshold_rule(
                        rule, remaining_production, context, consumption, timestamp
                    )
                elif rule.rule_type == RuleType.TIME_BASED:
                    allocation = _apply_time_based_rule(
                        rule, remaining_production, context
                    )
                elif rule.rule_type == RuleType.CONSUMPTION_BASED:
                    allocation = _apply_consumption_based_rule(
                        rule, remaining_production, context, consumption, timestamp
                    )
                else:
                    allocation = {}
                
                # Mettre à jour les allocations
                for site, amount in allocation.items():
                    if site not in allocations:
                        allocations[site] = 0
                    allocations[site] += amount
                    remaining_production -= amount
        
        # Allouer la production restante équitablement si nécessaire
        if remaining_production > 0.01 and consumption is not None:
            active_sites = [col for col in consumption.columns if consumption.loc[timestamp, col] > 0]
            if active_sites:
                per_site = remaining_production / len(active_sites)
                for site in active_sites:
                    if site not in allocations:
                        allocations[site] = 0
                    allocations[site] += per_site
        
        # Enregistrer les allocations
        for site, amount in allocations.items():
            column_name = f"Production_{site}"
            if column_name not in result.columns:
                result[column_name] = 0.0
            result.loc[timestamp, column_name] = amount
    
    # Ajouter les colonnes de vérification
    prod_columns = [c for c in result.columns if c.startswith('Production_')]
    result['_Total_Allocated'] = result[prod_columns].sum(axis=1)
    result['_Difference'] = production - result['_Total_Allocated']
    
    return result


def _apply_priority_rule(
    rule: RepartitionRule, 
    available_production: float,
    context: Dict,
    consumption: pd.DataFrame,
    timestamp: any
) -> Dict[str, float]:
    """Applique une règle de priorité"""
    allocations = {}
    
    # Obtenir l'ordre de priorité depuis les paramètres
    priority_order = rule.parameters.get('priority_order', rule.target_sites)
    
    remaining = available_production
    
    for site in priority_order:
        if remaining <= 0:
            break
        
        # Déterminer le besoin du site
        if consumption is not None and site in consumption.columns and timestamp in consumption.index:
            need = consumption.loc[timestamp, site]
        else:
            need = rule.parameters.get('default_need', 100)
        
        # Allouer selon le besoin et la disponibilité
        allocated = min(need, remaining)
        if allocated > 0:
            allocations[site] = allocated
            remaining -= allocated
    
    return allocations


def _apply_threshold_rule(
    rule: RepartitionRule,
    available_production: float,
    context: Dict,
    consumption: pd.DataFrame,
    timestamp: any
) -> Dict[str, float]:
    """Applique une règle de seuil"""
    allocations = {}
    
    min_threshold = rule.parameters.get('min_threshold', {})
    max_threshold = rule.parameters.get('max_threshold', {})
    
    # D'abord satisfaire les minimums
    remaining = available_production
    for site in rule.target_sites:
        if site in min_threshold:
            min_alloc = min_threshold[site]
            if min_alloc <= remaining:
                allocations[site] = min_alloc
                remaining -= min_alloc
    
    # Puis distribuer le reste en respectant les maximums
    if remaining > 0:
        sites_without_max = [s for s in rule.target_sites if s not in max_threshold]
        
        if sites_without_max:
            per_site = remaining / len(sites_without_max)
            for site in sites_without_max:
                allocations[site] = allocations.get(site, 0) + per_site
        else:
            # Distribuer proportionnellement selon les maximums
            for site in rule.target_sites:
                if site in max_threshold:
                    max_additional = max_threshold[site] - allocations.get(site, 0)
                    if max_additional > 0:
                        allocated = min(max_additional, remaining)
                        allocations[site] = allocations.get(site, 0) + allocated
                        remaining -= allocated
    
    return allocations


def _apply_time_based_rule(
    rule: RepartitionRule,
    available_production: float,
    context: Dict
) -> Dict[str, float]:
    """Applique une règle basée sur le temps"""
    allocations = {}
    
    # Obtenir les allocations selon l'heure
    time_allocations = rule.parameters.get('time_allocations', {})
    current_hour = context.get('hour', 0)
    
    # Trouver la configuration pour l'heure actuelle
    hour_key = str(current_hour)
    if hour_key in time_allocations:
        percentages = time_allocations[hour_key]
    else:
        # Utiliser la répartition par défaut
        percentages = rule.parameters.get('default_allocation', {})
    
    # Appliquer les pourcentages
    for site, percentage in percentages.items():
        if site in rule.target_sites:
            allocations[site] = available_production * (percentage / 100.0)
    
    return allocations


def _apply_consumption_based_rule(
    rule: RepartitionRule,
    available_production: float,
    context: Dict,
    consumption: pd.DataFrame,
    timestamp: any
) -> Dict[str, float]:
    """Applique une règle basée sur la consommation"""
    allocations = {}
    
    if consumption is None or consumption.empty:
        # Répartition équitable par défaut
        per_site = available_production / len(rule.target_sites)
        return {site: per_site for site in rule.target_sites}
    
    # Calculer la consommation totale des sites cibles
    total_consumption = 0
    site_consumptions = {}
    
    for site in rule.target_sites:
        if site in consumption.columns and timestamp in consumption.index:
            cons = consumption.loc[timestamp, site]
            site_consumptions[site] = cons
            total_consumption += cons
    
    if total_consumption == 0:
        # Répartition équitable si pas de consommation
        per_site = available_production / len(rule.target_sites)
        return {site: per_site for site in rule.target_sites}
    
    # Répartir proportionnellement à la consommation
    for site, cons in site_consumptions.items():
        proportion = cons / total_consumption
        allocations[site] = available_production * proportion
    
    return allocations


def optimize_repartition(
    production: pd.DataFrame,
    consumption: pd.DataFrame,
    sites_config: Dict,
    objective: str = 'maximize_self_consumption',
    constraints: Dict = None
) -> List[RepartitionKey]:
    """
    Optimisation automatique de la répartition selon objectifs
    
    Args:
        production: DataFrame avec la production totale
        consumption: DataFrame avec la consommation par site
        sites_config: Configuration des sites
        objective: Objectif d'optimisation
        constraints: Contraintes à respecter
        
    Returns:
        Liste optimisée de clés de répartition
    """
    if constraints is None:
        constraints = {}
    
    # Calculer les statistiques nécessaires
    total_production = production.sum().sum()
    site_consumptions = {}
    
    for site_id in sites_config.keys():
        if site_id in consumption.columns:
            site_consumptions[site_id] = consumption[site_id].sum()
        else:
            site_consumptions[site_id] = 0
    
    total_consumption = sum(site_consumptions.values())
    
    # Optimisation selon l'objectif
    if objective == 'maximize_self_consumption':
        # Maximiser l'autoconsommation globale
        keys = _optimize_for_self_consumption(
            sites_config, site_consumptions, total_production, total_consumption
        )
    
    elif objective == 'minimize_penalties':
        # Minimiser les pénalités de surplus
        keys = _optimize_for_minimal_penalties(
            sites_config, site_consumptions, total_production, constraints
        )
    
    elif objective == 'balance_savings':
        # Équilibrer les économies entre participants
        keys = _optimize_for_balanced_savings(
            sites_config, site_consumptions, total_production
        )
    
    else:
        # Par défaut : répartition proportionnelle à la consommation
        keys = []
        for site_id, site_data in sites_config.items():
            if total_consumption > 0:
                value = (site_consumptions.get(site_id, 0) / total_consumption) * 100
            else:
                value = 100.0 / len(sites_config)
            
            key = RepartitionKey(
                site_id=site_id,
                participant_name=site_data.get('nom_fichier', site_id),
                value=value
            )
            keys.append(key)
    
    return keys


def _optimize_for_self_consumption(
    sites_config: Dict,
    site_consumptions: Dict,
    total_production: float,
    total_consumption: float
) -> List[RepartitionKey]:
    """Optimise pour maximiser l'autoconsommation"""
    keys = []
    
    # Si la production est supérieure à la consommation totale
    if total_production >= total_consumption:
        # Allouer selon la consommation exacte
        for site_id, site_data in sites_config.items():
            consumption = site_consumptions.get(site_id, 0)
            value = (consumption / total_production) * 100 if total_production > 0 else 0
            
            key = RepartitionKey(
                site_id=site_id,
                participant_name=site_data.get('nom_fichier', site_id),
                value=min(value, 100.0)  # Limiter à 100%
            )
            keys.append(key)
    else:
        # Production insuffisante : répartir proportionnellement
        for site_id, site_data in sites_config.items():
            consumption = site_consumptions.get(site_id, 0)
            value = (consumption / total_consumption) * 100 if total_consumption > 0 else 0
            
            key = RepartitionKey(
                site_id=site_id,
                participant_name=site_data.get('nom_fichier', site_id),
                value=value
            )
            keys.append(key)
    
    # Normaliser pour que la somme fasse 100%
    total_allocated = sum(k.value for k in keys)
    if total_allocated > 0:
        for key in keys:
            key.value = (key.value / total_allocated) * 100
    
    return keys


def _optimize_for_minimal_penalties(
    sites_config: Dict,
    site_consumptions: Dict,
    total_production: float,
    constraints: Dict
) -> List[RepartitionKey]:
    """Optimise pour minimiser les pénalités"""
    # Implémentation simplifiée
    # TODO: Implémenter un algorithme plus sophistiqué avec les pénalités réelles
    return _optimize_for_self_consumption(
        sites_config, site_consumptions, total_production, sum(site_consumptions.values())
    )


def _optimize_for_balanced_savings(
    sites_config: Dict,
    site_consumptions: Dict,
    total_production: float
) -> List[RepartitionKey]:
    """Optimise pour équilibrer les économies"""
    keys = []
    
    # Calculer un ratio cible d'économies par site
    # Basé sur une combinaison de consommation et de taille
    site_weights = {}
    total_weight = 0
    
    for site_id, site_data in sites_config.items():
        # Poids basé sur la consommation et la puissance installée
        consumption_weight = site_consumptions.get(site_id, 0)
        power_weight = site_data.get('puissance_kwc', 0) * 100  # Facteur de normalisation
        
        weight = (consumption_weight + power_weight) / 2
        site_weights[site_id] = weight
        total_weight += weight
    
    # Allouer selon les poids
    for site_id, site_data in sites_config.items():
        if total_weight > 0:
            value = (site_weights[site_id] / total_weight) * 100
        else:
            value = 100.0 / len(sites_config)
        
        key = RepartitionKey(
            site_id=site_id,
            participant_name=site_data.get('nom_fichier', site_id),
            value=value
        )
        keys.append(key)
    
    return keys


def calculate_repartition_metrics(
    production_data: pd.DataFrame,
    allocated_data: pd.DataFrame,
    consumption_data: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Calcule les métriques de performance de la répartition
    
    Args:
        production_data: Production totale
        allocated_data: Production allouée par participant
        consumption_data: Consommation par participant (optionnel)
        
    Returns:
        Dict avec les métriques calculées
    """
    metrics = {
        'total_production': production_data.sum(),
        'total_allocated': allocated_data.sum().sum(),
        'allocation_efficiency': 0.0,
        'participant_metrics': {}
    }
    
    # Efficacité de l'allocation
    if metrics['total_production'] > 0:
        metrics['allocation_efficiency'] = (
            metrics['total_allocated'] / metrics['total_production']
        ) * 100
    
    # Métriques par participant
    for col in allocated_data.columns:
        if col.startswith('Production_'):
            participant = col.replace('Production_', '')
            
            participant_metrics = {
                'total_allocated': allocated_data[col].sum(),
                'average_allocation': allocated_data[col].mean(),
                'max_allocation': allocated_data[col].max(),
                'min_allocation': allocated_data[col].min()
            }
            
            # Si on a les données de consommation
            if consumption_data is not None and participant in consumption_data.columns:
                consumption = consumption_data[participant].sum()
                participant_metrics['total_consumption'] = consumption
                participant_metrics['self_consumption_rate'] = min(
                    participant_metrics['total_allocated'] / consumption * 100
                    if consumption > 0 else 0,
                    100.0
                )
            
            metrics['participant_metrics'][participant] = participant_metrics
    
    return metrics