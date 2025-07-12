"""Modèle de données pour l'autoconsommation collective.

Ce module définit les classes pour gérer l'autoconsommation collective,
incluant les allocations entre producteurs et consommateurs.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
import json


@dataclass
class CollectiveAutoAllocation:
    """Représente une allocation d'autoconsommation collective.
    
    Cette classe gère la relation entre un point de production
    et un client consommateur dans le cadre d'une opération
    d'autoconsommation collective.
    """
    
    # Champs obligatoires
    point_production_id: int
    client_id: int
    pourcentage_allocation: float
    date_debut: date
    
    # Champs optionnels
    id: Optional[int] = None
    date_fin: Optional[date] = None
    priorite: int = 1
    type_contrat: Optional[str] = None
    reference_contrat: Optional[str] = None
    notes: Optional[str] = None
    date_creation: Optional[datetime] = None
    
    # Champs calculés
    _production_allouee_kwh: Optional[float] = field(default=None, init=False)
    _statut: str = field(default='actif', init=False)
    
    def __post_init__(self):
        """Validation et initialisation après création."""
        # Validation du pourcentage
        if not 0 <= self.pourcentage_allocation <= 100:
            raise ValueError("Le pourcentage d'allocation doit être entre 0 et 100")
            
        # Validation des dates
        if self.date_fin and self.date_fin <= self.date_debut:
            raise ValueError("La date de fin doit être postérieure à la date de début")
            
        # Validation de la priorité
        if self.priorite < 1:
            raise ValueError("La priorité doit être >= 1")
            
        # Initialisation de la date de création
        if self.date_creation is None:
            self.date_creation = datetime.now()
            
        # Mise à jour du statut
        self._update_statut()
            
    def _update_statut(self):
        """Met à jour le statut de l'allocation."""
        today = date.today()
        
        if self.date_debut > today:
            self._statut = 'futur'
        elif self.date_fin and self.date_fin < today:
            self._statut = 'expiré'
        else:
            self._statut = 'actif'
            
    @property
    def is_active(self) -> bool:
        """Indique si l'allocation est actuellement active."""
        self._update_statut()
        return self._statut == 'actif'
        
    @property
    def statut(self) -> str:
        """Retourne le statut actuel de l'allocation."""
        self._update_statut()
        return self._statut
        
    @property
    def duree_jours(self) -> Optional[int]:
        """Calcule la durée de l'allocation en jours."""
        if self.date_fin:
            return (self.date_fin - self.date_debut).days
        return None
        
    def overlaps_with(self, other: 'CollectiveAutoAllocation') -> bool:
        """Vérifie si cette allocation chevauche avec une autre.
        
        Args:
            other: Autre allocation à comparer
            
        Returns:
            True si les périodes se chevauchent
        """
        # Vérifier d'abord si c'est le même producteur et client
        if (self.point_production_id != other.point_production_id or 
            self.client_id != other.client_id):
            return False
            
        # Déterminer les dates de fin effectives (None = infini)
        self_end = self.date_fin or date.max
        other_end = other.date_fin or date.max
        
        # Vérifier le chevauchement
        return not (self_end < other.date_debut or other_end < self.date_debut)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'id': self.id,
            'point_production_id': self.point_production_id,
            'client_id': self.client_id,
            'pourcentage_allocation': self.pourcentage_allocation,
            'date_debut': self.date_debut.isoformat(),
            'date_fin': self.date_fin.isoformat() if self.date_fin else None,
            'priorite': self.priorite,
            'type_contrat': self.type_contrat,
            'reference_contrat': self.reference_contrat,
            'notes': self.notes,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectiveAutoAllocation':
        """Crée une instance depuis un dictionnaire."""
        # Conversion des dates
        if 'date_debut' in data and isinstance(data['date_debut'], str):
            data['date_debut'] = date.fromisoformat(data['date_debut'])
        if 'date_fin' in data and isinstance(data['date_fin'], str):
            data['date_fin'] = date.fromisoformat(data['date_fin'])
        if 'date_creation' in data and isinstance(data['date_creation'], str):
            data['date_creation'] = datetime.fromisoformat(data['date_creation'])
            
        return cls(**data)


@dataclass
class CollectiveAutoOperation:
    """Représente une opération d'autoconsommation collective complète.
    
    Cette classe agrège toutes les allocations pour un point de production
    et fournit des méthodes pour gérer la capacité et les allocations.
    """
    
    point_production_id: int
    puissance_totale_kwc: float
    allocations: List[CollectiveAutoAllocation] = field(default_factory=list)
    
    @property
    def allocations_actives(self) -> List[CollectiveAutoAllocation]:
        """Retourne uniquement les allocations actives."""
        return [a for a in self.allocations if a.is_active]
        
    @property
    def pourcentage_total_alloue(self) -> float:
        """Calcule le pourcentage total alloué actuellement."""
        return sum(a.pourcentage_allocation for a in self.allocations_actives)
        
    @property
    def pourcentage_disponible(self) -> float:
        """Calcule le pourcentage de capacité disponible."""
        return max(0, 100 - self.pourcentage_total_alloue)
        
    @property
    def puissance_allouee_kwc(self) -> float:
        """Calcule la puissance totale allouée en kWc."""
        return self.puissance_totale_kwc * self.pourcentage_total_alloue / 100
        
    @property
    def puissance_disponible_kwc(self) -> float:
        """Calcule la puissance disponible en kWc."""
        return self.puissance_totale_kwc * self.pourcentage_disponible / 100
        
    @property
    def nombre_beneficiaires(self) -> int:
        """Compte le nombre de bénéficiaires actifs."""
        return len(set(a.client_id for a in self.allocations_actives))
        
    @property
    def taux_utilisation(self) -> float:
        """Calcule le taux d'utilisation de la capacité."""
        return self.pourcentage_total_alloue
        
    def can_allocate(self, pourcentage: float, exclude_allocation_id: int = None) -> bool:
        """Vérifie si on peut allouer un pourcentage donné.
        
        Args:
            pourcentage: Pourcentage à allouer
            exclude_allocation_id: ID d'allocation à exclure (pour modification)
            
        Returns:
            True si l'allocation est possible
        """
        total = sum(
            a.pourcentage_allocation 
            for a in self.allocations_actives 
            if a.id != exclude_allocation_id
        )
        return (total + pourcentage) <= 100
        
    def get_allocation_for_client(self, client_id: int) -> Optional[CollectiveAutoAllocation]:
        """Retourne l'allocation active pour un client donné."""
        for allocation in self.allocations_actives:
            if allocation.client_id == client_id:
                return allocation
        return None
        
    def get_allocations_by_priority(self) -> List[CollectiveAutoAllocation]:
        """Retourne les allocations triées par priorité."""
        return sorted(self.allocations_actives, key=lambda a: a.priorite)
        
    def simulate_new_allocation(self, client_id: int, pourcentage: float) -> Dict[str, Any]:
        """Simule l'ajout d'une nouvelle allocation.
        
        Args:
            client_id: ID du client
            pourcentage: Pourcentage à allouer
            
        Returns:
            Dictionnaire avec les résultats de la simulation
        """
        # Vérifier si le client a déjà une allocation
        existing = self.get_allocation_for_client(client_id)
        if existing:
            return {
                'possible': False,
                'raison': f"Le client a déjà une allocation de {existing.pourcentage_allocation}%",
                'allocation_existante': existing
            }
            
        # Vérifier la capacité
        if not self.can_allocate(pourcentage):
            return {
                'possible': False,
                'raison': f"Capacité insuffisante. Disponible: {self.pourcentage_disponible}%",
                'pourcentage_disponible': self.pourcentage_disponible
            }
            
        # Simulation OK
        return {
            'possible': True,
            'nouveau_total_alloue': self.pourcentage_total_alloue + pourcentage,
            'nouveau_disponible': self.pourcentage_disponible - pourcentage,
            'nouveau_nb_beneficiaires': self.nombre_beneficiaires + 1,
            'puissance_allouee_kwc': self.puissance_totale_kwc * pourcentage / 100
        }
        
    def optimize_allocations(self, target_utilization: float = 95.0) -> List[Dict[str, Any]]:
        """Optimise les allocations pour atteindre un taux d'utilisation cible.
        
        Args:
            target_utilization: Taux d'utilisation cible en %
            
        Returns:
            Liste de suggestions d'optimisation
        """
        suggestions = []
        current_utilization = self.taux_utilisation
        
        if current_utilization >= target_utilization:
            return [{
                'type': 'info',
                'message': f"Taux d'utilisation déjà optimal: {current_utilization:.1f}%"
            }]
            
        # Calculer l'augmentation nécessaire
        increase_needed = target_utilization - current_utilization
        
        # Suggérer une augmentation proportionnelle
        for allocation in self.allocations_actives:
            factor = 1 + (increase_needed / current_utilization)
            new_percentage = min(allocation.pourcentage_allocation * factor, 100)
            
            if new_percentage > allocation.pourcentage_allocation:
                suggestions.append({
                    'type': 'augmentation',
                    'client_id': allocation.client_id,
                    'allocation_actuelle': allocation.pourcentage_allocation,
                    'allocation_proposee': round(new_percentage, 1),
                    'augmentation': round(new_percentage - allocation.pourcentage_allocation, 1)
                })
                
        return suggestions
        
    def get_statistics(self) -> Dict[str, Any]:
        """Calcule des statistiques sur l'opération."""
        allocations_actives = self.allocations_actives
        
        if not allocations_actives:
            return {
                'nombre_beneficiaires': 0,
                'taux_utilisation': 0,
                'allocation_moyenne': 0,
                'allocation_min': 0,
                'allocation_max': 0,
                'puissance_totale_kwc': self.puissance_totale_kwc,
                'puissance_disponible_kwc': self.puissance_totale_kwc
            }
            
        pourcentages = [a.pourcentage_allocation for a in allocations_actives]
        
        return {
            'nombre_beneficiaires': self.nombre_beneficiaires,
            'taux_utilisation': self.taux_utilisation,
            'allocation_moyenne': sum(pourcentages) / len(pourcentages),
            'allocation_min': min(pourcentages),
            'allocation_max': max(pourcentages),
            'puissance_totale_kwc': self.puissance_totale_kwc,
            'puissance_allouee_kwc': self.puissance_allouee_kwc,
            'puissance_disponible_kwc': self.puissance_disponible_kwc,
            'nombre_allocations_futures': len([a for a in self.allocations if a.statut == 'futur']),
            'nombre_allocations_expirees': len([a for a in self.allocations if a.statut == 'expiré'])
        }