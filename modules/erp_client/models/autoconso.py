"""Modèles de données pour l'autoconsommation collective.

Ce module définit les structures de données pour gérer les opérations
d'autoconsommation collective entre producteurs et consommateurs.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Dict, Any
import json


@dataclass
class PointProduction:
    """Représente un point de production d'énergie."""
    
    id: Optional[int] = None
    client_id: int = None
    nom: str = ""
    type_installation: str = "Toiture"  # Toiture, Sol, Ombrière, Façade, Autre
    capacite_kwc: float = 0.0
    capacite_disponible_kwc: float = 0.0
    date_mise_service: Optional[date] = None
    adresse: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    actif: bool = True
    notes: Optional[str] = None
    date_creation: Optional[datetime] = None
    date_modification: Optional[datetime] = None
    
    # Champs calculés/jointure
    client_nom: Optional[str] = None
    nombre_allocations: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'nom': self.nom,
            'type_installation': self.type_installation,
            'capacite_kwc': self.capacite_kwc,
            'capacite_disponible_kwc': self.capacite_disponible_kwc,
            'date_mise_service': self.date_mise_service.isoformat() if self.date_mise_service else None,
            'adresse': self.adresse,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'actif': self.actif,
            'notes': self.notes,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'date_modification': self.date_modification.isoformat() if self.date_modification else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PointProduction':
        """Crée une instance depuis un dictionnaire."""
        # Gérer les dates
        if data.get('date_mise_service'):
            if isinstance(data['date_mise_service'], str):
                data['date_mise_service'] = date.fromisoformat(data['date_mise_service'])
                
        if data.get('date_creation'):
            if isinstance(data['date_creation'], str):
                data['date_creation'] = datetime.fromisoformat(data['date_creation'])
                
        if data.get('date_modification'):
            if isinstance(data['date_modification'], str):
                data['date_modification'] = datetime.fromisoformat(data['date_modification'])
                
        return cls(**data)
    
    def validate(self) -> list[str]:
        """Valide les données du point de production."""
        errors = []
        
        if not self.client_id:
            errors.append("Client requis")
            
        if not self.nom:
            errors.append("Nom requis")
            
        if self.capacite_kwc <= 0:
            errors.append("Capacité doit être positive")
            
        if self.capacite_disponible_kwc < 0:
            errors.append("Capacité disponible ne peut être négative")
            
        if self.capacite_disponible_kwc > self.capacite_kwc:
            errors.append("Capacité disponible ne peut dépasser la capacité totale")
            
        return errors


@dataclass
class PointConsommation:
    """Représente un point de consommation d'énergie."""
    
    id: Optional[int] = None
    client_id: int = None
    reference_interne: str = ""  # PDL, numéro compteur, etc.
    type_point: str = "Principal"  # Principal, Secondaire, Auxiliaire
    consommation_annuelle_kwh: float = 0.0
    puissance_souscrite_kva: int = 36
    adresse: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    actif: bool = True
    notes: Optional[str] = None
    date_creation: Optional[datetime] = None
    date_modification: Optional[datetime] = None
    
    # Champs calculés/jointure
    client_nom: Optional[str] = None
    allocation_active: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'reference_interne': self.reference_interne,
            'type_point': self.type_point,
            'consommation_annuelle_kwh': self.consommation_annuelle_kwh,
            'puissance_souscrite_kva': self.puissance_souscrite_kva,
            'adresse': self.adresse,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'actif': self.actif,
            'notes': self.notes,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'date_modification': self.date_modification.isoformat() if self.date_modification else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PointConsommation':
        """Crée une instance depuis un dictionnaire."""
        # Gérer les dates
        if data.get('date_creation'):
            if isinstance(data['date_creation'], str):
                data['date_creation'] = datetime.fromisoformat(data['date_creation'])
                
        if data.get('date_modification'):
            if isinstance(data['date_modification'], str):
                data['date_modification'] = datetime.fromisoformat(data['date_modification'])
                
        return cls(**data)
    
    def validate(self) -> list[str]:
        """Valide les données du point de consommation."""
        errors = []
        
        if not self.client_id:
            errors.append("Client requis")
            
        if not self.reference_interne:
            errors.append("Référence interne requise")
            
        if self.consommation_annuelle_kwh < 0:
            errors.append("Consommation ne peut être négative")
            
        if self.puissance_souscrite_kva not in [3, 6, 9, 12, 15, 18, 24, 30, 36, 42, 48, 54, 60, 
                                                72, 84, 96, 108, 120, 132, 144, 156, 168, 180, 
                                                192, 204, 216, 228, 240, 252]:
            errors.append("Puissance souscrite invalide")
            
        return errors


@dataclass
class AutoconsoCollective:
    """Représente une allocation d'autoconsommation collective."""
    
    id: Optional[int] = None
    point_production_id: int = None
    point_consommation_id: int = None
    pourcentage_allocation: float = 0.0
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    actif: bool = True
    notes: Optional[str] = None
    date_creation: Optional[datetime] = None
    date_modification: Optional[datetime] = None
    
    # Champs calculés/jointure
    point_production_nom: Optional[str] = None
    point_consommation_ref: Optional[str] = None
    client_producteur_nom: Optional[str] = None
    client_consommateur_nom: Optional[str] = None
    capacite_allouee_kwc: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'id': self.id,
            'point_production_id': self.point_production_id,
            'point_consommation_id': self.point_consommation_id,
            'pourcentage_allocation': self.pourcentage_allocation,
            'date_debut': self.date_debut.isoformat() if self.date_debut else None,
            'date_fin': self.date_fin.isoformat() if self.date_fin else None,
            'actif': self.actif,
            'notes': self.notes,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'date_modification': self.date_modification.isoformat() if self.date_modification else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoconsoCollective':
        """Crée une instance depuis un dictionnaire."""
        # Gérer les dates
        if data.get('date_debut'):
            if isinstance(data['date_debut'], str):
                data['date_debut'] = date.fromisoformat(data['date_debut'])
                
        if data.get('date_fin'):
            if isinstance(data['date_fin'], str):
                data['date_fin'] = date.fromisoformat(data['date_fin'])
                
        if data.get('date_creation'):
            if isinstance(data['date_creation'], str):
                data['date_creation'] = datetime.fromisoformat(data['date_creation'])
                
        if data.get('date_modification'):
            if isinstance(data['date_modification'], str):
                data['date_modification'] = datetime.fromisoformat(data['date_modification'])
                
        return cls(**data)
    
    def validate(self) -> list[str]:
        """Valide les données de l'allocation."""
        errors = []
        
        if not self.point_production_id:
            errors.append("Point de production requis")
            
        if not self.point_consommation_id:
            errors.append("Point de consommation requis")
            
        if self.pourcentage_allocation <= 0 or self.pourcentage_allocation > 100:
            errors.append("Pourcentage doit être entre 1 et 100")
            
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            errors.append("Date de fin ne peut être avant la date de début")
            
        return errors
    
    @property
    def is_active(self) -> bool:
        """Vérifie si l'allocation est actuellement active."""
        if not self.actif:
            return False
            
        today = date.today()
        
        if self.date_debut and today < self.date_debut:
            return False
            
        if self.date_fin and today > self.date_fin:
            return False
            
        return True