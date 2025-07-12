"""Modèle de données pour les points de production.

Ce module définit la classe ProductionPoint pour gérer
les installations de production d'énergie solaire.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import json


@dataclass
class ProductionPoint:
    """Représente un point de production d'énergie solaire.
    
    Attributes:
        id: Identifiant unique
        nom: Nom du site de production
        code_site: Code unique du site
        puissance_kwc: Puissance installée en kWc
        latitude: Latitude GPS
        longitude: Longitude GPS
        adresse: Adresse du site
        date_mise_service: Date de mise en service
        type_installation: Type d'installation (toiture, sol, ombrière, etc.)
        technologie: Technologie des panneaux
        inclinaison: Angle d'inclinaison des panneaux (0-90°)
        orientation: Orientation des panneaux (0-360°, 0=Nord, 180=Sud)
        productible_annuel_kwh: Production annuelle estimée en kWh
        metadata: Données techniques additionnelles
        actif: Statut actif/inactif
        date_creation: Date de création dans le système
    """
    
    # Champs obligatoires
    nom: str
    puissance_kwc: float
    
    # Champs optionnels
    id: Optional[int] = None
    code_site: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    adresse: Optional[str] = None
    date_mise_service: Optional[date] = None
    type_installation: Optional[str] = None
    technologie: Optional[str] = None
    inclinaison: Optional[int] = None
    orientation: Optional[int] = None
    productible_annuel_kwh: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    actif: bool = True
    date_creation: Optional[datetime] = None
    
    # Champs calculés
    _capacite_disponible: Optional[float] = field(default=None, init=False)
    _allocations: List[Dict] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """Validation et initialisation après création."""
        # Validation de la puissance
        if self.puissance_kwc <= 0:
            raise ValueError("La puissance doit être positive")
            
        # Génération du code site si non fourni
        if not self.code_site:
            self.code_site = self._generate_code_site()
            
        # Validation de l'inclinaison
        if self.inclinaison is not None:
            if not 0 <= self.inclinaison <= 90:
                raise ValueError("L'inclinaison doit être entre 0 et 90 degrés")
                
        # Validation de l'orientation
        if self.orientation is not None:
            if not 0 <= self.orientation < 360:
                raise ValueError("L'orientation doit être entre 0 et 359 degrés")
                
        # Initialisation de la date de création
        if self.date_creation is None:
            self.date_creation = datetime.now()
            
    def _generate_code_site(self) -> str:
        """Génère un code site unique basé sur le nom et la date."""
        # Prendre les 3 premières lettres du nom (ou moins si nom court)
        prefix = ''.join(c for c in self.nom.upper() if c.isalnum())[:3]
        # Ajouter timestamp pour unicité
        timestamp = datetime.now().strftime("%y%m%d%H%M")
        return f"PROD-{prefix}-{timestamp}"
        
    @property
    def age_annees(self) -> Optional[float]:
        """Calcule l'âge de l'installation en années."""
        if self.date_mise_service:
            delta = datetime.now().date() - self.date_mise_service
            return delta.days / 365.25
        return None
        
    @property
    def facteur_capacite(self) -> Optional[float]:
        """Calcule le facteur de capacité (ratio production/puissance)."""
        if self.productible_annuel_kwh and self.puissance_kwc > 0:
            # Nombre d'heures dans une année
            heures_annee = 8760
            return self.productible_annuel_kwh / (self.puissance_kwc * heures_annee)
        return None
        
    @property
    def production_specifique(self) -> Optional[float]:
        """Calcule la production spécifique en kWh/kWc."""
        if self.productible_annuel_kwh and self.puissance_kwc > 0:
            return self.productible_annuel_kwh / self.puissance_kwc
        return None
        
    @property
    def orientation_str(self) -> str:
        """Retourne l'orientation sous forme textuelle."""
        if self.orientation is None:
            return "Non définie"
            
        # Conversion orientation en texte
        if 337.5 <= self.orientation or self.orientation < 22.5:
            return "Nord"
        elif 22.5 <= self.orientation < 67.5:
            return "Nord-Est"
        elif 67.5 <= self.orientation < 112.5:
            return "Est"
        elif 112.5 <= self.orientation < 157.5:
            return "Sud-Est"
        elif 157.5 <= self.orientation < 202.5:
            return "Sud"
        elif 202.5 <= self.orientation < 247.5:
            return "Sud-Ouest"
        elif 247.5 <= self.orientation < 292.5:
            return "Ouest"
        elif 292.5 <= self.orientation < 337.5:
            return "Nord-Ouest"
            
    @property
    def has_coordinates(self) -> bool:
        """Indique si le point a des coordonnées GPS."""
        return self.latitude is not None and self.longitude is not None
        
    def calculate_monthly_production(self, month: int) -> float:
        """Estime la production mensuelle basée sur des profils types.
        
        Args:
            month: Numéro du mois (1-12)
            
        Returns:
            Production estimée en kWh pour le mois
        """
        if not self.productible_annuel_kwh:
            return 0.0
            
        # Profil de production mensuel typique (% de la production annuelle)
        # Basé sur des données moyennes France
        profil_mensuel = {
            1: 0.04,   # Janvier
            2: 0.05,   # Février
            3: 0.08,   # Mars
            4: 0.10,   # Avril
            5: 0.12,   # Mai
            6: 0.13,   # Juin
            7: 0.14,   # Juillet
            8: 0.13,   # Août
            9: 0.10,   # Septembre
            10: 0.07,  # Octobre
            11: 0.05,  # Novembre
            12: 0.04   # Décembre
        }
        
        return self.productible_annuel_kwh * profil_mensuel.get(month, 0.08)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire.
        
        Returns:
            Dictionnaire contenant toutes les données
        """
        data = {
            'id': self.id,
            'nom': self.nom,
            'code_site': self.code_site,
            'puissance_kwc': self.puissance_kwc,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'adresse': self.adresse,
            'date_mise_service': self.date_mise_service.isoformat() if self.date_mise_service else None,
            'type_installation': self.type_installation,
            'technologie': self.technologie,
            'inclinaison': self.inclinaison,
            'orientation': self.orientation,
            'productible_annuel_kwh': self.productible_annuel_kwh,
            'metadata': json.dumps(self.metadata) if self.metadata else '{}',
            'actif': self.actif,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }
        
        return {k: v for k, v in data.items() if v is not None}
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductionPoint':
        """Crée une instance depuis un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données
            
        Returns:
            Instance de ProductionPoint
        """
        # Conversion des dates
        if 'date_mise_service' in data and isinstance(data['date_mise_service'], str):
            data['date_mise_service'] = date.fromisoformat(data['date_mise_service'])
        if 'date_creation' in data and isinstance(data['date_creation'], str):
            data['date_creation'] = datetime.fromisoformat(data['date_creation'])
            
        # Conversion des metadata
        if 'metadata' in data and isinstance(data['metadata'], str):
            try:
                data['metadata'] = json.loads(data['metadata'])
            except json.JSONDecodeError:
                data['metadata'] = {}
                
        return cls(**data)
        
    def validate(self) -> List[str]:
        """Valide les données du point de production.
        
        Returns:
            Liste des erreurs de validation
        """
        errors = []
        
        # Validation du nom
        if not self.nom or len(self.nom.strip()) == 0:
            errors.append("Le nom du site est obligatoire")
        elif len(self.nom) > 200:
            errors.append("Le nom ne doit pas dépasser 200 caractères")
            
        # Validation de la puissance
        if self.puissance_kwc <= 0:
            errors.append("La puissance doit être positive")
        elif self.puissance_kwc > 100000:  # 100 MWc max
            errors.append("La puissance semble trop élevée (max 100 MWc)")
            
        # Validation du code site
        if self.code_site and len(self.code_site) > 50:
            errors.append("Le code site ne doit pas dépasser 50 caractères")
            
        # Validation des coordonnées
        if self.latitude is not None:
            if not -90 <= self.latitude <= 90:
                errors.append("La latitude doit être comprise entre -90 et 90")
        if self.longitude is not None:
            if not -180 <= self.longitude <= 180:
                errors.append("La longitude doit être comprise entre -180 et 180")
                
        # Validation de l'inclinaison
        if self.inclinaison is not None:
            if not 0 <= self.inclinaison <= 90:
                errors.append("L'inclinaison doit être entre 0 et 90 degrés")
                
        # Validation de l'orientation
        if self.orientation is not None:
            if not 0 <= self.orientation < 360:
                errors.append("L'orientation doit être entre 0 et 359 degrés")
                
        # Validation du productible
        if self.productible_annuel_kwh is not None:
            if self.productible_annuel_kwh < 0:
                errors.append("Le productible ne peut pas être négatif")
            # Vérification cohérence avec puissance (800-1400 kWh/kWc typique)
            if self.puissance_kwc > 0:
                ratio = self.productible_annuel_kwh / self.puissance_kwc
                if ratio < 500 or ratio > 2000:
                    errors.append(f"Le productible spécifique ({ratio:.0f} kWh/kWc) semble incohérent")
                    
        # Validation de la date de mise en service
        if self.date_mise_service:
            if self.date_mise_service > date.today():
                errors.append("La date de mise en service ne peut pas être dans le futur")
            elif self.date_mise_service.year < 1950:
                errors.append("La date de mise en service semble trop ancienne")
                
        # Validation du type d'installation
        if self.type_installation:
            types_valides = ['toiture', 'sol', 'ombrière', 'façade', 'flottant', 'autre']
            if self.type_installation.lower() not in types_valides:
                errors.append(f"Type d'installation non reconnu. Types valides: {', '.join(types_valides)}")
                
        return errors
        
    def __str__(self) -> str:
        """Représentation string du point de production."""
        return f"ProductionPoint({self.code_site}: {self.nom} - {self.puissance_kwc} kWc)"
        
    def __repr__(self) -> str:
        """Représentation détaillée."""
        return (f"ProductionPoint(id={self.id}, code_site='{self.code_site}', "
                f"nom='{self.nom}', puissance={self.puissance_kwc} kWc)")