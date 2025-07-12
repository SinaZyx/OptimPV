"""Modèles de données pour la gestion des prix clients.

Ce module contient les classes de données pour la tarification,
incluant les prix personnalisés et les types de tarifs.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
import json


class TypeTarif(Enum):
    """Types de tarifs disponibles."""
    FIXE = "fixe"
    INDEXE = "indexe"
    DYNAMIQUE = "dynamique"


@dataclass
class PrixClient:
    """Représente un prix client."""
    id: Optional[int]
    client_id: int
    prix_kwh: float
    date_debut: date
    date_fin: Optional[date]
    type_tarif: str
    reference_prix: Optional[str]
    remise_pourcentage: float
    formule_calcul: Optional[Dict[str, Any]]
    notes: Optional[str]
    date_creation: Optional[datetime]
    
    def is_active(self, check_date: date = None) -> bool:
        """Vérifie si le prix est actif à une date donnée."""
        if check_date is None:
            check_date = date.today()
            
        if self.date_debut > check_date:
            return False
            
        if self.date_fin and self.date_fin < check_date:
            return False
            
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour la base de données."""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'prix_kwh': self.prix_kwh,
            'date_debut': self.date_debut.isoformat(),
            'date_fin': self.date_fin.isoformat() if self.date_fin else None,
            'type_tarif': self.type_tarif,
            'reference_prix': self.reference_prix,
            'remise_pourcentage': self.remise_pourcentage,
            'formule_calcul': json.dumps(self.formule_calcul) if self.formule_calcul else None,
            'notes': self.notes,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }