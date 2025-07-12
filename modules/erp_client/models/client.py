"""Modèle de données pour les clients.

Ce module définit la classe Client et ses méthodes associées
pour la gestion des données clients dans le système ERP.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import json


class TypeClient(Enum):
    """Énumération des types de clients."""
    PRODUCTEUR = "producteur"
    CONSOMMATEUR = "consommateur"
    PROSUMER = "prosumer"


@dataclass
class Client:
    """Représente un client dans le système ERP.
    
    Attributes:
        id: Identifiant unique du client
        code_client: Code client unique
        nom: Nom du client
        type_client: Type de client (producteur, consommateur, prosumer)
        adresse: Adresse complète
        code_postal: Code postal
        ville: Ville
        latitude: Latitude GPS
        longitude: Longitude GPS
        zone_geographique: Zone géographique d'appartenance
        telephone: Numéro de téléphone
        email: Adresse email
        siret: Numéro SIRET
        contact_principal: Nom du contact principal
        notes: Notes libres
        metadata: Métadonnées additionnelles (JSON)
        date_creation: Date de création
        date_modification: Date de dernière modification
        actif: Statut actif/inactif
    """
    
    # Champs obligatoires
    code_client: str
    nom: str
    type_client: TypeClient
    
    # Champs optionnels avec valeurs par défaut
    id: Optional[int] = None
    adresse: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone_geographique: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    siret: Optional[str] = None
    contact_principal: Optional[str] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    date_creation: Optional[datetime] = None
    date_modification: Optional[datetime] = None
    actif: bool = True
    
    # Champs calculés (non stockés en base)
    _prix_actuel: Optional[float] = field(default=None, init=False)
    _allocations_autoconso: List[Dict] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """Validation et initialisation après création."""
        # Conversion string vers enum si nécessaire
        if isinstance(self.type_client, str):
            try:
                self.type_client = TypeClient(self.type_client.lower())
            except ValueError:
                raise ValueError(f"Type client invalide: {self.type_client}. Doit être parmi {[t.value for t in TypeClient]}")
        
        # Validation du type de client
        if not isinstance(self.type_client, TypeClient):
            raise ValueError(f"Type client invalide: {self.type_client}. Doit être une instance de TypeClient")
            
        # Validation du code client
        if not self.code_client or len(self.code_client.strip()) == 0:
            raise ValueError("Le code client ne peut pas être vide")
            
        # Nettoyage des chaînes
        self.code_client = self.code_client.strip().upper()
        self.nom = self.nom.strip()
        
        # Initialisation des dates si non fournies
        if self.date_creation is None:
            self.date_creation = datetime.now()
        if self.date_modification is None:
            self.date_modification = self.date_creation
            
    @property
    def nom_complet(self) -> str:
        """Retourne le nom complet avec le code client."""
        return f"{self.nom} ({self.code_client})"
        
    @property
    def adresse_complete(self) -> str:
        """Retourne l'adresse complète formatée."""
        parts = []
        if self.adresse:
            parts.append(self.adresse)
        if self.code_postal and self.ville:
            parts.append(f"{self.code_postal} {self.ville}")
        elif self.ville:
            parts.append(self.ville)
            
        return ", ".join(parts) if parts else "Adresse non renseignée"
        
    @property
    def has_coordinates(self) -> bool:
        """Indique si le client a des coordonnées GPS."""
        return self.latitude is not None and self.longitude is not None
        
    @property
    def is_producteur(self) -> bool:
        """Indique si le client est producteur."""
        return self.type_client in [TypeClient.PRODUCTEUR, TypeClient.PROSUMER]
        
    @property
    def is_consommateur(self) -> bool:
        """Indique si le client est consommateur."""
        return self.type_client in [TypeClient.CONSOMMATEUR, TypeClient.PROSUMER]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire contenant toutes les données du client
        """
        data = {
            'id': self.id,
            'code_client': self.code_client,
            'nom': self.nom,
            'type_client': self.type_client.value if isinstance(self.type_client, TypeClient) else self.type_client,
            'adresse': self.adresse,
            'code_postal': self.code_postal,
            'ville': self.ville,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'zone_geographique': self.zone_geographique,
            'telephone': self.telephone,
            'email': self.email,
            'siret': self.siret,
            'contact_principal': self.contact_principal,
            'notes': self.notes,
            'metadata': json.dumps(self.metadata) if self.metadata else '{}',
            'date_creation': self.date_creation.isoformat() if self.date_creation else None,
            'date_modification': self.date_modification.isoformat() if self.date_modification else None,
            'actif': self.actif
        }
        
        # Retirer les valeurs None pour l'insertion en base
        return {k: v for k, v in data.items() if v is not None}
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Client':
        """Crée une instance Client depuis un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données du client
            
        Returns:
            Instance de Client
        """
        # Conversion des dates string en datetime
        if 'date_creation' in data and isinstance(data['date_creation'], str):
            data['date_creation'] = datetime.fromisoformat(data['date_creation'])
        if 'date_modification' in data and isinstance(data['date_modification'], str):
            data['date_modification'] = datetime.fromisoformat(data['date_modification'])
            
        # Conversion des metadata JSON en dict
        if 'metadata' in data and isinstance(data['metadata'], str):
            try:
                data['metadata'] = json.loads(data['metadata'])
            except json.JSONDecodeError:
                data['metadata'] = {}
        
        # Conversion du type client string vers enum
        if 'type_client' in data and isinstance(data['type_client'], str):
            try:
                data['type_client'] = TypeClient(data['type_client'].lower())
            except ValueError:
                # Garder la valeur string pour que la validation dans __post_init__ puisse la traiter
                pass
                
        return cls(**data)
        
    def validate(self) -> List[str]:
        """Valide les données du client.
        
        Returns:
            Liste des erreurs de validation (vide si tout est OK)
        """
        errors = []
        
        # Validation du code client
        if not self.code_client or len(self.code_client.strip()) == 0:
            errors.append("Le code client est obligatoire")
        elif len(self.code_client) > 50:
            errors.append("Le code client ne doit pas dépasser 50 caractères")
            
        # Validation du nom
        if not self.nom or len(self.nom.strip()) == 0:
            errors.append("Le nom du client est obligatoire")
        elif len(self.nom) > 200:
            errors.append("Le nom ne doit pas dépasser 200 caractères")
            
        # Validation du type
        if not isinstance(self.type_client, TypeClient):
            errors.append(f"Le type client doit être une instance de TypeClient")
            
        # Validation email
        if self.email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                errors.append("L'adresse email n'est pas valide")
                
        # Validation SIRET (14 chiffres)
        if self.siret:
            siret_clean = self.siret.replace(' ', '').replace('-', '')
            if not siret_clean.isdigit() or len(siret_clean) != 14:
                errors.append("Le SIRET doit contenir exactement 14 chiffres")
                
        # Validation coordonnées GPS
        if self.latitude is not None:
            if not -90 <= self.latitude <= 90:
                errors.append("La latitude doit être comprise entre -90 et 90")
        if self.longitude is not None:
            if not -180 <= self.longitude <= 180:
                errors.append("La longitude doit être comprise entre -180 et 180")
                
        return errors
        
    def update_from(self, other: 'Client'):
        """Met à jour les données depuis un autre objet Client.
        
        Args:
            other: Autre instance de Client
        """
        # Ne pas mettre à jour l'ID et les dates de création
        skip_fields = ['id', 'date_creation', 'date_modification']
        
        for field_name in self.__dataclass_fields__:
            if field_name not in skip_fields:
                setattr(self, field_name, getattr(other, field_name))
                
        # Mettre à jour la date de modification
        self.date_modification = datetime.now()
        
    def __str__(self) -> str:
        """Représentation string du client."""
        return f"Client({self.code_client}: {self.nom} - {self.type_client})"
        
    def __repr__(self) -> str:
        """Représentation détaillée du client."""
        return (f"Client(id={self.id}, code_client='{self.code_client}', "
                f"nom='{self.nom}', type_client='{self.type_client}', "
                f"actif={self.actif})")