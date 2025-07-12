"""Modèle de données pour les points de consommation.

Ce module définit la classe ConsumptionPoint pour gérer
les points de consommation d'énergie des clients.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import json


@dataclass
class ConsumptionPoint:
    """Représente un point de consommation d'énergie.
    
    Attributes:
        id: Identifiant unique
        client_id: ID du client propriétaire
        nom: Nom du point de consommation
        code_pdl: Point de livraison (PDL/PRM)
        adresse: Adresse du point
        puissance_souscrite_kva: Puissance souscrite en kVA
        type_compteur: Type de compteur (Linky, électronique, mécanique)
        type_tarif: Type de tarification (Base, HP/HC, Tempo, etc.)
        consommation_annuelle_kwh: Consommation annuelle estimée
        profil_type: Profil de consommation type
        secteur_activite: Secteur d'activité (résidentiel, tertiaire, industriel)
        metadata: Données additionnelles
        actif: Statut actif/inactif
        date_creation: Date de création dans le système
    """
    
    # Champs obligatoires
    client_id: int
    nom: str
    
    # Champs optionnels
    id: Optional[int] = None
    code_pdl: Optional[str] = None
    adresse: Optional[str] = None
    puissance_souscrite_kva: Optional[float] = None
    type_compteur: Optional[str] = None
    type_tarif: Optional[str] = None
    consommation_annuelle_kwh: Optional[float] = None
    profil_type: Optional[str] = None
    secteur_activite: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    actif: bool = True
    date_creation: Optional[datetime] = None
    
    # Champs calculés
    _historique_conso: List[Dict] = field(default_factory=list, init=False)
    _previsions_conso: List[Dict] = field(default_factory=list, init=False)
    
    def __post_init__(self):
        """Validation et initialisation après création."""
        # Validation du nom
        if not self.nom or len(self.nom.strip()) == 0:
            raise ValueError("Le nom du point de consommation est obligatoire")
            
        # Nettoyage des chaînes
        self.nom = self.nom.strip()
        if self.code_pdl:
            self.code_pdl = self.code_pdl.strip().upper()
            
        # Initialisation de la date
        if self.date_creation is None:
            self.date_creation = datetime.now()
            
    @property
    def consommation_mensuelle_moyenne(self) -> float:
        """Calcule la consommation mensuelle moyenne."""
        if self.consommation_annuelle_kwh:
            return self.consommation_annuelle_kwh / 12
        return 0.0
        
    @property
    def consommation_journaliere_moyenne(self) -> float:
        """Calcule la consommation journalière moyenne."""
        if self.consommation_annuelle_kwh:
            return self.consommation_annuelle_kwh / 365
        return 0.0
        
    @property
    def puissance_max_kw(self) -> Optional[float]:
        """Convertit la puissance souscrite de kVA en kW (facteur 0.9)."""
        if self.puissance_souscrite_kva:
            return self.puissance_souscrite_kva * 0.9
        return None
        
    def calculate_monthly_consumption(self, month: int) -> float:
        """Estime la consommation mensuelle selon le profil type.
        
        Args:
            month: Numéro du mois (1-12)
            
        Returns:
            Consommation estimée en kWh pour le mois
        """
        if not self.consommation_annuelle_kwh:
            return 0.0
            
        # Profils de consommation mensuels selon le secteur
        profils = {
            'résidentiel': {
                1: 0.12, 2: 0.11, 3: 0.10, 4: 0.08,
                5: 0.07, 6: 0.06, 7: 0.06, 8: 0.06,
                9: 0.07, 10: 0.08, 11: 0.10, 12: 0.11
            },
            'tertiaire': {
                1: 0.10, 2: 0.09, 3: 0.09, 4: 0.08,
                5: 0.08, 6: 0.08, 7: 0.07, 8: 0.07,
                9: 0.08, 10: 0.08, 11: 0.09, 12: 0.09
            },
            'industriel': {
                1: 0.09, 2: 0.09, 3: 0.09, 4: 0.08,
                5: 0.08, 6: 0.08, 7: 0.07, 8: 0.07,
                9: 0.08, 10: 0.09, 11: 0.09, 12: 0.09
            }
        }
        
        # Profil par défaut si secteur non défini
        profil = profils.get(self.secteur_activite, profils['résidentiel'])
        return self.consommation_annuelle_kwh * profil.get(month, 0.083)
        
    def calculate_hourly_profile(self, hour: int, is_weekend: bool = False) -> float:
        """Calcule le profil de charge horaire (% de la consommation journalière).
        
        Args:
            hour: Heure de la journée (0-23)
            is_weekend: True si weekend
            
        Returns:
            Pourcentage de la consommation journalière pour cette heure
        """
        # Profils horaires typiques
        if self.secteur_activite == 'résidentiel':
            if is_weekend:
                profil = [
                    0.02, 0.02, 0.02, 0.02, 0.02, 0.03,  # 0h-5h
                    0.04, 0.05, 0.06, 0.06, 0.05, 0.05,  # 6h-11h
                    0.06, 0.05, 0.04, 0.04, 0.04, 0.05,  # 12h-17h
                    0.06, 0.07, 0.07, 0.06, 0.04, 0.03   # 18h-23h
                ]
            else:
                profil = [
                    0.02, 0.02, 0.02, 0.02, 0.02, 0.03,  # 0h-5h
                    0.05, 0.06, 0.05, 0.04, 0.03, 0.03,  # 6h-11h
                    0.04, 0.03, 0.03, 0.03, 0.04, 0.05,  # 12h-17h
                    0.07, 0.08, 0.08, 0.07, 0.05, 0.03   # 18h-23h
                ]
        elif self.secteur_activite == 'tertiaire':
            if is_weekend:
                profil = [0.02] * 24  # Consommation minimale le weekend
            else:
                profil = [
                    0.01, 0.01, 0.01, 0.01, 0.01, 0.01,  # 0h-5h
                    0.02, 0.04, 0.07, 0.08, 0.08, 0.08,  # 6h-11h
                    0.07, 0.08, 0.08, 0.08, 0.07, 0.06,  # 12h-17h
                    0.04, 0.03, 0.02, 0.02, 0.01, 0.01   # 18h-23h
                ]
        else:  # industriel
            # Profil 3x8 typique
            profil = [0.04] * 24  # Consommation constante 24/7
            
        return profil[hour] if 0 <= hour < 24 else 0.0
        
    def estimate_autoconso_potential(self, production_profile: List[float]) -> Dict[str, float]:
        """Estime le potentiel d'autoconsommation.
        
        Args:
            production_profile: Profil de production horaire (24 valeurs)
            
        Returns:
            Dictionnaire avec taux d'autoconso, autoproduction, etc.
        """
        if len(production_profile) != 24:
            raise ValueError("Le profil de production doit contenir 24 valeurs")
            
        # Calcul sur une journée type
        conso_jour = self.consommation_journaliere_moyenne
        
        autoconso_kwh = 0.0
        for hour in range(24):
            conso_heure = conso_jour * self.calculate_hourly_profile(hour)
            prod_heure = production_profile[hour]
            autoconso_kwh += min(conso_heure, prod_heure)
            
        production_totale = sum(production_profile)
        
        return {
            'autoconso_kwh': autoconso_kwh,
            'taux_autoconso': autoconso_kwh / production_totale if production_totale > 0 else 0,
            'taux_autoproduction': autoconso_kwh / conso_jour if conso_jour > 0 else 0,
            'surplus_kwh': production_totale - autoconso_kwh
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        data = {
            'id': self.id,
            'client_id': self.client_id,
            'nom': self.nom,
            'code_pdl': self.code_pdl,
            'adresse': self.adresse,
            'puissance_souscrite_kva': self.puissance_souscrite_kva,
            'type_compteur': self.type_compteur,
            'type_tarif': self.type_tarif,
            'consommation_annuelle_kwh': self.consommation_annuelle_kwh,
            'profil_type': self.profil_type,
            'secteur_activite': self.secteur_activite,
            'metadata': json.dumps(self.metadata) if self.metadata else '{}',
            'actif': self.actif,
            'date_creation': self.date_creation.isoformat() if self.date_creation else None
        }
        
        return {k: v for k, v in data.items() if v is not None}
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsumptionPoint':
        """Crée une instance depuis un dictionnaire."""
        # Conversion de la date
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
        """Valide les données du point de consommation."""
        errors = []
        
        # Validation du nom
        if not self.nom or len(self.nom.strip()) == 0:
            errors.append("Le nom est obligatoire")
        elif len(self.nom) > 200:
            errors.append("Le nom ne doit pas dépasser 200 caractères")
            
        # Validation du code PDL (14 chiffres typiquement)
        if self.code_pdl:
            pdl_clean = self.code_pdl.replace(' ', '').replace('-', '')
            if not pdl_clean.isdigit() or len(pdl_clean) != 14:
                errors.append("Le code PDL doit contenir 14 chiffres")
                
        # Validation de la puissance souscrite
        if self.puissance_souscrite_kva is not None:
            if self.puissance_souscrite_kva <= 0:
                errors.append("La puissance souscrite doit être positive")
            # Valeurs standard: 3, 6, 9, 12, 15, 18, 24, 30, 36 kVA
            valeurs_standard = [3, 6, 9, 12, 15, 18, 24, 30, 36]
            if self.puissance_souscrite_kva not in valeurs_standard:
                # Accepter aussi les puissances industrielles
                if self.puissance_souscrite_kva < 36:
                    errors.append(f"Puissance non standard. Valeurs courantes: {valeurs_standard}")
                    
        # Validation du type de compteur
        if self.type_compteur:
            types_valides = ['Linky', 'électronique', 'mécanique', 'PME-PMI']
            if self.type_compteur not in types_valides:
                errors.append(f"Type de compteur invalide. Types valides: {', '.join(types_valides)}")
                
        # Validation du type de tarif
        if self.type_tarif:
            tarifs_valides = ['Base', 'HP/HC', 'Tempo', 'EJP', 'Vert', 'Jaune']
            if self.type_tarif not in tarifs_valides:
                errors.append(f"Type de tarif invalide. Tarifs valides: {', '.join(tarifs_valides)}")
                
        # Validation de la consommation
        if self.consommation_annuelle_kwh is not None:
            if self.consommation_annuelle_kwh < 0:
                errors.append("La consommation ne peut pas être négative")
            # Vérification cohérence avec puissance
            if self.puissance_souscrite_kva and self.puissance_souscrite_kva > 0:
                # Facteur d'utilisation typique: 1000-8000 h/an
                heures_equiv = self.consommation_annuelle_kwh / (self.puissance_souscrite_kva * 0.9)
                if heures_equiv > 8760:
                    errors.append("La consommation semble trop élevée par rapport à la puissance")
                    
        # Validation du secteur d'activité
        if self.secteur_activite:
            secteurs_valides = ['résidentiel', 'tertiaire', 'industriel', 'agricole', 'autre']
            if self.secteur_activite not in secteurs_valides:
                errors.append(f"Secteur invalide. Secteurs valides: {', '.join(secteurs_valides)}")
                
        return errors
        
    def __str__(self) -> str:
        """Représentation string."""
        pdl = f" ({self.code_pdl})" if self.code_pdl else ""
        return f"ConsumptionPoint({self.nom}{pdl})"
        
    def __repr__(self) -> str:
        """Représentation détaillée."""
        return (f"ConsumptionPoint(id={self.id}, client_id={self.client_id}, "
                f"nom='{self.nom}', puissance={self.puissance_souscrite_kva} kVA)")