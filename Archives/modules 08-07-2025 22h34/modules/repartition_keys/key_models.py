"""
Modèles de données pour la gestion des clés de répartition
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Literal
from enum import Enum
import json


class KeyType(Enum):
    """Types de clés de répartition"""
    STATIC = "static"
    DYNAMIC = "dynamic"
    RULE_BASED = "rule_based"


class PeriodType(Enum):
    """Types de périodes de répartition"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RuleType(Enum):
    """Types de règles de répartition"""
    PRIORITY = "priority"
    THRESHOLD = "threshold"
    TIME_BASED = "time_based"
    CONSUMPTION_BASED = "consumption_based"
    PRODUCTION_BASED = "production_based"


@dataclass
class RepartitionKey:
    """Modèle pour une clé de répartition"""
    site_id: str
    participant_name: str
    value: float  # Pourcentage de 0 à 100
    key_type: KeyType = KeyType.STATIC
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        # Validation de la valeur
        if not 0 <= self.value <= 100:
            raise ValueError(f"La valeur de la clé doit être entre 0 et 100, reçu: {self.value}")
        
        # Conversion string vers enum si nécessaire
        if isinstance(self.key_type, str):
            self.key_type = KeyType(self.key_type)
    
    def to_dict(self) -> Dict:
        """Convertit l'objet en dictionnaire"""
        return {
            'site_id': self.site_id,
            'participant_name': self.participant_name,
            'value': self.value,
            'key_type': self.key_type.value,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RepartitionKey':
        """Crée un objet depuis un dictionnaire"""
        data = data.copy()
        if 'period_start' in data and data['period_start']:
            data['period_start'] = datetime.fromisoformat(data['period_start'])
        if 'period_end' in data and data['period_end']:
            data['period_end'] = datetime.fromisoformat(data['period_end'])
        return cls(**data)


@dataclass
class RepartitionPeriod:
    """Période de répartition avec ensemble de clés"""
    period_id: str
    period_type: PeriodType
    period_name: str
    keys: List[RepartitionKey] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.period_type, str):
            self.period_type = PeriodType(self.period_type)
    
    @property
    def total_validation(self) -> bool:
        """Vérifie que la somme des clés fait 100%"""
        total = sum(key.value for key in self.keys)
        return abs(total - 100.0) < 0.01  # Tolérance pour les erreurs d'arrondi
    
    @property
    def validation_details(self) -> Dict:
        """Retourne les détails de validation"""
        total = sum(key.value for key in self.keys)
        return {
            'is_valid': self.total_validation,
            'total': total,
            'difference': 100.0 - total,
            'key_count': len(self.keys)
        }
    
    def get_key_for_site(self, site_id: str) -> Optional[RepartitionKey]:
        """Retourne la clé pour un site donné"""
        for key in self.keys:
            if key.site_id == site_id:
                return key
        return None
    
    def to_dict(self) -> Dict:
        """Convertit l'objet en dictionnaire"""
        return {
            'period_id': self.period_id,
            'period_type': self.period_type.value,
            'period_name': self.period_name,
            'keys': [key.to_dict() for key in self.keys],
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'validation': self.validation_details
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RepartitionPeriod':
        """Crée un objet depuis un dictionnaire"""
        data = data.copy()
        if 'keys' in data:
            data['keys'] = [RepartitionKey.from_dict(k) for k in data['keys']]
        if 'start_date' in data and data['start_date']:
            data['start_date'] = datetime.fromisoformat(data['start_date'])
        if 'end_date' in data and data['end_date']:
            data['end_date'] = datetime.fromisoformat(data['end_date'])
        # Retirer validation qui n'est pas un paramètre du constructeur
        data.pop('validation', None)
        return cls(**data)


@dataclass
class RepartitionCondition:
    """Condition pour une règle de répartition"""
    field: str  # Ex: "consumption", "time_of_day", "production"
    operator: Literal["<", "<=", ">", ">=", "==", "!=", "in", "not_in"]
    value: any
    
    def evaluate(self, context: Dict) -> bool:
        """Évalue la condition dans un contexte donné"""
        if self.field not in context:
            return False
        
        field_value = context[self.field]
        
        if self.operator == "<":
            return field_value < self.value
        elif self.operator == "<=":
            return field_value <= self.value
        elif self.operator == ">":
            return field_value > self.value
        elif self.operator == ">=":
            return field_value >= self.value
        elif self.operator == "==":
            return field_value == self.value
        elif self.operator == "!=":
            return field_value != self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        else:
            raise ValueError(f"Opérateur non supporté: {self.operator}")
    
    def to_dict(self) -> Dict:
        return {
            'field': self.field,
            'operator': self.operator,
            'value': self.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RepartitionCondition':
        return cls(**data)


@dataclass
class RepartitionRule:
    """Règle de répartition dynamique"""
    rule_id: str
    rule_name: str
    rule_type: RuleType
    priority: int = 0  # Plus le nombre est élevé, plus la priorité est haute
    parameters: Dict = field(default_factory=dict)
    conditions: List[RepartitionCondition] = field(default_factory=list)
    target_sites: List[str] = field(default_factory=list)  # Sites concernés par la règle
    enabled: bool = True
    
    def __post_init__(self):
        if isinstance(self.rule_type, str):
            self.rule_type = RuleType(self.rule_type)
        
        # Convertir les conditions si nécessaire
        conditions_converted = []
        for cond in self.conditions:
            if isinstance(cond, dict):
                conditions_converted.append(RepartitionCondition.from_dict(cond))
            else:
                conditions_converted.append(cond)
        self.conditions = conditions_converted
    
    def applies_to_context(self, context: Dict) -> bool:
        """Vérifie si la règle s'applique dans le contexte donné"""
        if not self.enabled:
            return False
        
        # Vérifier toutes les conditions
        return all(condition.evaluate(context) for condition in self.conditions)
    
    def to_dict(self) -> Dict:
        """Convertit l'objet en dictionnaire"""
        return {
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'rule_type': self.rule_type.value,
            'priority': self.priority,
            'parameters': self.parameters,
            'conditions': [cond.to_dict() for cond in self.conditions],
            'target_sites': self.target_sites,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RepartitionRule':
        """Crée un objet depuis un dictionnaire"""
        return cls(**data)


@dataclass
class RepartitionTemplate:
    """Template prédéfini de répartition"""
    template_id: str
    template_name: str
    description: str
    template_type: Literal["equitable", "consumption_based", "priority", "custom"]
    keys_pattern: Dict[str, float] = field(default_factory=dict)
    rules: List[RepartitionRule] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def apply_to_sites(self, sites_config: Dict) -> List[RepartitionKey]:
        """Applique le template aux sites configurés"""
        keys = []
        
        if self.template_type == "equitable":
            # Répartition équitable entre tous les sites
            site_count = len(sites_config)
            if site_count > 0:
                value_per_site = 100.0 / site_count
                for site_id, site_data in sites_config.items():
                    keys.append(RepartitionKey(
                        site_id=site_id,
                        participant_name=site_data.get('nom_fichier', site_id),
                        value=value_per_site,
                        key_type=KeyType.STATIC
                    ))
        
        elif self.template_type == "consumption_based":
            # Répartition basée sur la consommation historique
            # À implémenter selon les données disponibles
            pass
        
        elif self.template_type == "priority":
            # Répartition selon les priorités définies
            # À implémenter selon les règles
            pass
        
        elif self.template_type == "custom":
            # Utiliser le pattern défini
            for site_id, value in self.keys_pattern.items():
                if site_id in sites_config:
                    keys.append(RepartitionKey(
                        site_id=site_id,
                        participant_name=sites_config[site_id].get('nom_fichier', site_id),
                        value=value,
                        key_type=KeyType.STATIC
                    ))
        
        return keys
    
    def to_dict(self) -> Dict:
        """Convertit l'objet en dictionnaire"""
        return {
            'template_id': self.template_id,
            'template_name': self.template_name,
            'description': self.description,
            'template_type': self.template_type,
            'keys_pattern': self.keys_pattern,
            'rules': [rule.to_dict() for rule in self.rules],
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RepartitionTemplate':
        """Crée un objet depuis un dictionnaire"""
        data = data.copy()
        if 'rules' in data:
            data['rules'] = [RepartitionRule.from_dict(r) for r in data['rules']]
        return cls(**data)