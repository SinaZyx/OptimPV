"""Service métier pour la gestion des capacités d'autoconsommation collective.

Ce module gère l'allocation des capacités de production entre les consommateurs,
l'optimisation des répartitions et le suivi des taux d'utilisation.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date
import json

from ..database.erp_database import ERPDatabase
from ..models.autoconso import PointProduction, PointConsommation, AutoconsoCollective

logger = logging.getLogger(__name__)


class CapacityService:
    """Service pour la gestion des capacités d'autoconsommation collective."""
    
    def __init__(self, db_path: str = None):
        """Initialise le service de capacité.
        
        Args:
            db_path: Chemin vers la base de données
        """
        self.db = ERPDatabase(db_path)
        
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du dashboard."""
        stats = {
            'total_production_points': 0,
            'active_production_points': 0,
            'total_capacity_kwc': 0,
            'available_capacity_kwc': 0,
            'total_consumption_points': 0,
            'active_allocations': 0,
            'average_utilization': 0
        }
        
        # Points de production
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN actif THEN 1 ELSE 0 END) as actifs,
                SUM(capacite_kwc) as capacite_totale,
                SUM(capacite_kwc - (
                    SELECT COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0)
                    FROM autoconso_collective ac
                    WHERE ac.point_production_id = pp.id 
                    AND ac.actif = TRUE
                    AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
                )) as capacite_disponible
            FROM points_production pp
        """
        
        result = self.db.execute_query(query)
        if result:
            stats['total_production_points'] = result[0]['total'] or 0
            stats['active_production_points'] = result[0]['actifs'] or 0
            stats['total_capacity_kwc'] = result[0]['capacite_totale'] or 0
            stats['available_capacity_kwc'] = result[0]['capacite_disponible'] or 0
            
        # Points de consommation
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN pc.id IN (
                    SELECT point_consommation_id 
                    FROM autoconso_collective 
                    WHERE actif = TRUE
                ) THEN 1 ELSE 0 END) as avec_allocation
            FROM points_consommation pc
            WHERE pc.actif = TRUE
        """
        
        result = self.db.execute_query(query)
        if result:
            stats['total_consumption_points'] = result[0]['total'] or 0
            stats['active_allocations'] = result[0]['avec_allocation'] or 0
            
        # Calcul utilisation moyenne
        if stats['total_capacity_kwc'] > 0:
            utilized = stats['total_capacity_kwc'] - stats['available_capacity_kwc']
            stats['average_utilization'] = (utilized / stats['total_capacity_kwc']) * 100
            
        return stats
    
    def get_capacity_alerts(self) -> List[Dict[str, Any]]:
        """Récupère les alertes de capacité."""
        alerts = []
        
        query = """
            SELECT 
                pp.id,
                pp.nom,
                pp.capacite_kwc,
                COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) as capacite_utilisee
            FROM points_production pp
            LEFT JOIN autoconso_collective ac ON pp.id = ac.point_production_id 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            WHERE pp.actif = TRUE
            GROUP BY pp.id, pp.nom, pp.capacite_kwc
        """
        
        results = self.db.execute_query(query)
        
        for row in results:
            if row['capacite_kwc'] > 0:
                utilization = (row['capacite_utilisee'] / row['capacite_kwc']) * 100
                
                if utilization >= 95:
                    alerts.append({
                        'level': 'critical',
                        'point_name': row['nom'],
                        'utilization': utilization,
                        'message': 'Capacité presque saturée'
                    })
                elif utilization >= 90:
                    alerts.append({
                        'level': 'warning',
                        'point_name': row['nom'],
                        'utilization': utilization,
                        'message': 'Capacité élevée'
                    })
                elif utilization >= 80:
                    alerts.append({
                        'level': 'info',
                        'point_name': row['nom'],
                        'utilization': utilization,
                        'message': 'Seuil d\'alerte atteint'
                    })
                    
        return sorted(alerts, key=lambda x: x['utilization'], reverse=True)
    
    def get_production_summary(self) -> List[Dict[str, Any]]:
        """Récupère le résumé des points de production."""
        query = """
            SELECT 
                pp.nom as name,
                pp.capacite_kwc as capacity_kwc,
                c.nom as client_name
            FROM points_production pp
            JOIN clients c ON pp.client_id = c.id
            WHERE pp.actif = TRUE
            ORDER BY pp.capacite_kwc DESC
        """
        
        return self.db.execute_query(query)
    
    def get_utilization_by_point(self) -> List[Dict[str, Any]]:
        """Récupère le taux d'utilisation par point."""
        query = """
            SELECT 
                pp.nom as name,
                pp.capacite_kwc,
                COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) as capacite_utilisee,
                CASE 
                    WHEN pp.capacite_kwc > 0 
                    THEN (COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) / pp.capacite_kwc * 100)
                    ELSE 0 
                END as utilization_percent
            FROM points_production pp
            LEFT JOIN autoconso_collective ac ON pp.id = ac.point_production_id 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            WHERE pp.actif = TRUE
            GROUP BY pp.id, pp.nom, pp.capacite_kwc
            ORDER BY utilization_percent DESC
        """
        
        return self.db.execute_query(query)
    
    def get_all_production_points(self) -> List[PointProduction]:
        """Récupère tous les points de production."""
        query = """
            SELECT 
                pp.*,
                c.nom as client_nom,
                COUNT(DISTINCT ac.id) as nombre_allocations,
                pp.capacite_kwc - COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) as capacite_disponible_kwc
            FROM points_production pp
            JOIN clients c ON pp.client_id = c.id
            LEFT JOIN autoconso_collective ac ON pp.id = ac.point_production_id 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            GROUP BY pp.id, c.nom
            ORDER BY pp.nom
        """
        
        results = self.db.execute_query(query)
        return [PointProduction.from_dict(row) for row in results]
    
    def create_production_point(self, point: PointProduction) -> PointProduction:
        """Crée un nouveau point de production."""
        errors = point.validate()
        if errors:
            raise ValueError(f"Erreurs de validation: {', '.join(errors)}")
            
        data = point.to_dict()
        data.pop('id', None)
        data['capacite_disponible_kwc'] = data['capacite_kwc']  # Au début, toute la capacité est disponible
        
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        query = f"""
            INSERT INTO points_production ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        point_id = self.db.execute_command(query, tuple(data.values()))
        point.id = point_id
        
        logger.info(f"Point de production créé: {point.nom} (ID: {point_id})")
        return point
    
    def get_point_utilization(self, point_id: int) -> float:
        """Calcule le taux d'utilisation d'un point."""
        query = """
            SELECT 
                pp.capacite_kwc,
                COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) as capacite_utilisee
            FROM points_production pp
            LEFT JOIN autoconso_collective ac ON pp.id = ac.point_production_id 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            WHERE pp.id = ?
            GROUP BY pp.capacite_kwc
        """
        
        result = self.db.execute_query(query, (point_id,))
        if result and result[0]['capacite_kwc'] > 0:
            return (result[0]['capacite_utilisee'] / result[0]['capacite_kwc']) * 100
        return 0
    
    def deactivate_production_point(self, point_id: int) -> bool:
        """Désactive un point de production."""
        query = "UPDATE points_production SET actif = FALSE WHERE id = ?"
        rows = self.db.execute_command(query, (point_id,))
        return rows > 0
    
    def activate_production_point(self, point_id: int) -> bool:
        """Active un point de production."""
        query = "UPDATE points_production SET actif = TRUE WHERE id = ?"
        rows = self.db.execute_command(query, (point_id,))
        return rows > 0
    
    def get_allocations_for_production(self, production_id: int) -> List[AutoconsoCollective]:
        """Récupère les allocations d'un point de production."""
        query = """
            SELECT 
                ac.*,
                pp.nom as point_production_nom,
                pc.reference_interne as point_consommation_ref,
                cp.nom as client_producteur_nom,
                cc.nom as client_consommateur_nom,
                pp.capacite_kwc * ac.pourcentage_allocation / 100 as capacite_allouee_kwc
            FROM autoconso_collective ac
            JOIN points_production pp ON ac.point_production_id = pp.id
            JOIN points_consommation pc ON ac.point_consommation_id = pc.id
            JOIN clients cp ON pp.client_id = cp.id
            JOIN clients cc ON pc.client_id = cc.id
            WHERE ac.point_production_id = ?
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            ORDER BY ac.pourcentage_allocation DESC
        """
        
        results = self.db.execute_query(query, (production_id,))
        return [AutoconsoCollective.from_dict(row) for row in results]
    
    def get_production_points_with_availability(self) -> List[Dict[str, Any]]:
        """Récupère les points de production avec leur capacité disponible."""
        query = """
            SELECT 
                pp.id,
                pp.nom as name,
                pp.capacite_kwc as total_capacity,
                pp.capacite_kwc - COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) as available_capacity
            FROM points_production pp
            LEFT JOIN autoconso_collective ac ON pp.id = ac.point_production_id 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            WHERE pp.actif = TRUE
            GROUP BY pp.id, pp.nom, pp.capacite_kwc
            HAVING available_capacity > 0
            ORDER BY available_capacity DESC
        """
        
        return self.db.execute_query(query)
    
    def get_all_consumption_points(self) -> List[PointConsommation]:
        """Récupère tous les points de consommation."""
        query = """
            SELECT 
                pc.*,
                c.nom as client_nom,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM autoconso_collective ac 
                        WHERE ac.point_consommation_id = pc.id 
                        AND ac.actif = TRUE
                        AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
                    ) THEN TRUE 
                    ELSE FALSE 
                END as allocation_active
            FROM points_consommation pc
            JOIN clients c ON pc.client_id = c.id
            WHERE pc.actif = TRUE
            ORDER BY c.nom, pc.reference_interne
        """
        
        results = self.db.execute_query(query)
        return [PointConsommation.from_dict(row) for row in results]
    
    def create_consumption_point(self, point: PointConsommation) -> PointConsommation:
        """Crée un nouveau point de consommation."""
        errors = point.validate()
        if errors:
            raise ValueError(f"Erreurs de validation: {', '.join(errors)}")
            
        data = point.to_dict()
        data.pop('id', None)
        
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        query = f"""
            INSERT INTO points_consommation ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        point_id = self.db.execute_command(query, tuple(data.values()))
        point.id = point_id
        
        logger.info(f"Point de consommation créé: {point.reference_interne} (ID: {point_id})")
        return point
    
    def get_unallocated_consumption_points(self) -> List[PointConsommation]:
        """Récupère les points de consommation non alloués."""
        query = """
            SELECT 
                pc.*,
                c.nom as client_nom
            FROM points_consommation pc
            JOIN clients c ON pc.client_id = c.id
            WHERE pc.actif = TRUE
                AND NOT EXISTS (
                    SELECT 1 FROM autoconso_collective ac 
                    WHERE ac.point_consommation_id = pc.id 
                    AND ac.actif = TRUE
                    AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
                )
            ORDER BY c.nom, pc.reference_interne
        """
        
        results = self.db.execute_query(query)
        return [PointConsommation.from_dict(row) for row in results]
    
    def get_allocation_for_consumption(self, consumption_id: int) -> Optional[AutoconsoCollective]:
        """Récupère l'allocation active d'un point de consommation."""
        query = """
            SELECT 
                ac.*,
                pp.nom as point_production_nom,
                pc.reference_interne as point_consommation_ref,
                cp.nom as client_producteur_nom,
                cc.nom as client_consommateur_nom,
                pp.capacite_kwc * ac.pourcentage_allocation / 100 as capacite_allouee_kwc
            FROM autoconso_collective ac
            JOIN points_production pp ON ac.point_production_id = pp.id
            JOIN points_consommation pc ON ac.point_consommation_id = pc.id
            JOIN clients cp ON pp.client_id = cp.id
            JOIN clients cc ON pc.client_id = cc.id
            WHERE ac.point_consommation_id = ?
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            LIMIT 1
        """
        
        results = self.db.execute_query(query, (consumption_id,))
        if results:
            return AutoconsoCollective.from_dict(results[0])
        return None
    
    def delete_consumption_point(self, point_id: int) -> bool:
        """Supprime (désactive) un point de consommation."""
        query = "UPDATE points_consommation SET actif = FALSE WHERE id = ?"
        rows = self.db.execute_command(query, (point_id,))
        return rows > 0
    
    def create_allocation(self, allocation: AutoconsoCollective) -> AutoconsoCollective:
        """Crée une nouvelle allocation."""
        errors = allocation.validate()
        if errors:
            raise ValueError(f"Erreurs de validation: {', '.join(errors)}")
            
        # Vérifier la capacité disponible
        capacity_check = self._check_available_capacity(
            allocation.point_production_id,
            allocation.pourcentage_allocation
        )
        if not capacity_check['available']:
            raise ValueError(capacity_check['message'])
            
        # Vérifier que le point de consommation n'est pas déjà alloué
        existing = self.get_allocation_for_consumption(allocation.point_consommation_id)
        if existing:
            raise ValueError("Ce point de consommation a déjà une allocation active")
            
        data = allocation.to_dict()
        data.pop('id', None)
        
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        query = f"""
            INSERT INTO autoconso_collective ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        allocation_id = self.db.execute_command(query, tuple(data.values()))
        allocation.id = allocation_id
        
        logger.info(f"Allocation créée: ID {allocation_id}")
        return allocation
    
    def _check_available_capacity(self, production_id: int, requested_percentage: float) -> Dict[str, Any]:
        """Vérifie la capacité disponible pour une allocation."""
        query = """
            SELECT 
                pp.nom,
                pp.capacite_kwc,
                COALESCE(SUM(ac.pourcentage_allocation), 0) as pourcentage_utilise
            FROM points_production pp
            LEFT JOIN autoconso_collective ac ON pp.id = ac.point_production_id 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            WHERE pp.id = ?
            GROUP BY pp.id, pp.nom, pp.capacite_kwc
        """
        
        result = self.db.execute_query(query, (production_id,))
        
        if not result:
            return {
                'available': False,
                'message': "Point de production introuvable"
            }
            
        row = result[0]
        pourcentage_disponible = 100 - row['pourcentage_utilise']
        
        if requested_percentage > pourcentage_disponible:
            return {
                'available': False,
                'message': f"Capacité insuffisante sur {row['nom']}. Disponible: {pourcentage_disponible:.1f}%"
            }
            
        return {
            'available': True,
            'message': "Capacité disponible",
            'remaining_percentage': pourcentage_disponible - requested_percentage
        }
    
    def get_all_active_allocations(self) -> List[AutoconsoCollective]:
        """Récupère toutes les allocations actives."""
        query = """
            SELECT 
                ac.*,
                pp.nom as point_production_nom,
                pc.reference_interne as point_consommation_ref,
                cp.nom as client_producteur_nom,
                cc.nom as client_consommateur_nom,
                pp.capacite_kwc * ac.pourcentage_allocation / 100 as capacite_allouee_kwc
            FROM autoconso_collective ac
            JOIN points_production pp ON ac.point_production_id = pp.id
            JOIN points_consommation pc ON ac.point_consommation_id = pc.id
            JOIN clients cp ON pp.client_id = cp.id
            JOIN clients cc ON pc.client_id = cc.id
            WHERE ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            ORDER BY pp.nom, ac.pourcentage_allocation DESC
        """
        
        results = self.db.execute_query(query)
        return [AutoconsoCollective.from_dict(row) for row in results]
    
    def end_allocation(self, allocation_id: int) -> bool:
        """Termine une allocation."""
        query = """
            UPDATE autoconso_collective 
            SET date_fin = DATE('now'), 
                actif = FALSE,
                date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        
        rows = self.db.execute_command(query, (allocation_id,))
        return rows > 0
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Génère des suggestions d'optimisation."""
        suggestions = []
        
        # Suggestion 1: Points de production sous-utilisés
        query = """
            SELECT 
                pp.id,
                pp.nom,
                pp.capacite_kwc,
                pp.capacite_kwc - COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) as capacite_disponible
            FROM points_production pp
            LEFT JOIN autoconso_collective ac ON pp.id = ac.point_production_id 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            WHERE pp.actif = TRUE
            GROUP BY pp.id, pp.nom, pp.capacite_kwc
            HAVING capacite_disponible > pp.capacite_kwc * 0.2
        """
        
        results = self.db.execute_query(query)
        for row in results:
            suggestions.append({
                'type': 'new_client',
                'production_point': row['nom'],
                'capacity': row['capacite_disponible'],
                'client_name': 'Nouveau client potentiel'
            })
            
        # Suggestion 2: Points proches de saturation
        utilization_data = self.get_utilization_by_point()
        for point in utilization_data:
            if point['utilization_percent'] > 85:
                suggestions.append({
                    'type': 'capacity_warning',
                    'production_point': point['name'],
                    'utilization': point['utilization_percent']
                })
                
        return suggestions
    
    def get_capacity_utilization(self, production_point_id: int) -> float:
        """Calcule le taux d'utilisation d'un point de production.
        
        Args:
            production_point_id: ID du point de production
            
        Returns:
            Pourcentage d'utilisation (0-100)
        """
        return self.get_point_utilization(production_point_id)
    
    def get_total_capacity(self) -> float:
        """Récupère la capacité totale installée en kWc.
        
        Returns:
            Capacité totale en kWc
        """
        try:
            query = """
                SELECT COALESCE(SUM(capacite_kwc), 0) as total_capacity
                FROM points_production 
                WHERE actif = TRUE
            """
            
            result = self.db.execute_query(query)
            if result and len(result) > 0:
                return float(result[0]['total_capacity'] or 0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la capacité totale: {e}")
            return 0.0
    
    def get_client_capacity(self, client_id: int) -> float:
        """Récupère la capacité allouée à un client.
        
        Args:
            client_id: ID du client
            
        Returns:
            Capacité allouée en kWc
        """
        try:
            query = """
                SELECT COALESCE(SUM(pp.capacite_kwc * ac.pourcentage_allocation / 100), 0) as client_capacity
                FROM autoconso_collective ac
                JOIN points_production pp ON ac.point_production_id = pp.id
                JOIN points_consommation pc ON ac.point_consommation_id = pc.id
                WHERE pc.client_id = ? 
                AND ac.actif = TRUE
                AND (ac.date_fin IS NULL OR ac.date_fin >= DATE('now'))
            """
            
            result = self.db.execute_query(query, (client_id,))
            if result and len(result) > 0:
                return float(result[0]['client_capacity'] or 0)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la capacité client {client_id}: {e}")
            return 0.0