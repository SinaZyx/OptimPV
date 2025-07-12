"""Service métier pour la gestion des prix clients.

Ce module gère toute la logique tarifaire incluant les prix personnalisés,
l'historique, les formules dynamiques et les projections.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, date, timedelta
import json
import math

from ..database.erp_database import ERPDatabase
from ..models.pricing import PrixClient

logger = logging.getLogger(__name__)



class PricingService:
    """Service pour la gestion des prix clients."""
    
    # Prix de référence par défaut (à mettre à jour régulièrement)
    PRIX_REFERENCES = {
        'EDF_TRV_BASE': 0.2276,  # Tarif réglementé base 2024
        'EDF_TRV_HP': 0.2460,    # Heures pleines
        'EDF_TRV_HC': 0.1828,    # Heures creuses
        'SPOT_MOYEN': 0.1500,    # Prix spot moyen estimé
        'PPA_STANDARD': 0.1200   # Prix PPA standard
    }
    
    def __init__(self, db_path: str = None):
        """Initialise le service de prix.
        
        Args:
            db_path: Chemin vers la base de données
        """
        self.db = ERPDatabase(db_path)
        
    def create_prix(self, prix: PrixClient) -> PrixClient:
        """Crée un nouveau prix pour un client.
        
        Args:
            prix: Prix à créer
            
        Returns:
            Prix créé avec son ID
            
        Raises:
            ValueError: Si validation échoue
        """
        # Validation
        self._validate_prix(prix)
        
        # Vérifier les chevauchements
        if self._check_overlap(prix):
            raise ValueError("Le prix chevauche avec une période existante")
            
        # Préparer les données
        data = prix.to_dict()
        data.pop('id', None)
        
        # Requête d'insertion
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        query = f"""
            INSERT INTO prix_clients ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        try:
            prix_id = self.db.execute_command(query, tuple(data.values()))
            prix.id = prix_id
            
            logger.info(f"Prix créé pour client {prix.client_id}: {prix.prix_kwh} €/kWh")
            return prix
            
        except Exception as e:
            logger.error(f"Erreur création prix: {e}")
            raise
            
    def update_prix(self, prix: PrixClient) -> PrixClient:
        """Met à jour un prix existant.
        
        Args:
            prix: Prix à mettre à jour
            
        Returns:
            Prix mis à jour
        """
        if not prix.id:
            raise ValueError("ID requis pour la mise à jour")
            
        # Validation
        self._validate_prix(prix)
        
        # Vérifier les chevauchements (en excluant ce prix)
        if self._check_overlap(prix, exclude_id=prix.id):
            raise ValueError("Le prix chevauche avec une période existante")
            
        # Préparer les données
        data = prix.to_dict()
        data.pop('id')
        data.pop('date_creation', None)
        
        # Requête de mise à jour
        set_clauses = [f"{col} = ?" for col in data.keys()]
        query = f"""
            UPDATE prix_clients
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """
        
        try:
            values = list(data.values()) + [prix.id]
            self.db.execute_command(query, values)
            
            logger.info(f"Prix mis à jour: ID {prix.id}")
            return prix
            
        except Exception as e:
            logger.error(f"Erreur mise à jour prix: {e}")
            raise
            
    def get_active_price(self, client_id: int, check_date: date = None) -> Optional[PrixClient]:
        """Récupère le prix actif pour un client à une date donnée.
        
        Args:
            client_id: ID du client
            check_date: Date de vérification (par défaut aujourd'hui)
            
        Returns:
            Prix actif ou None
        """
        if check_date is None:
            check_date = date.today()
            
        query = """
            SELECT * FROM prix_clients
            WHERE client_id = ?
              AND date_debut <= ?
              AND (date_fin IS NULL OR date_fin >= ?)
            ORDER BY date_debut DESC
            LIMIT 1
        """
        
        results = self.db.execute_query(
            query, 
            (client_id, check_date.isoformat(), check_date.isoformat())
        )
        
        if results:
            return self._prix_from_dict(results[0])
        return None
        
    def get_price_history(self, client_id: int) -> List[PrixClient]:
        """Récupère l'historique complet des prix d'un client.
        
        Args:
            client_id: ID du client
            
        Returns:
            Liste des prix triés par date
        """
        query = """
            SELECT * FROM prix_clients
            WHERE client_id = ?
            ORDER BY date_debut DESC
        """
        
        results = self.db.execute_query(query, (client_id,))
        return [self._prix_from_dict(row) for row in results]
        
    def calculate_dynamic_price(
        self, 
        base_price: float,
        formula: Dict[str, Any],
        reference_date: date = None
    ) -> float:
        """Calcule un prix dynamique selon une formule.
        
        Args:
            base_price: Prix de base
            formula: Formule de calcul
            reference_date: Date de référence
            
        Returns:
            Prix calculé
        """
        if reference_date is None:
            reference_date = date.today()
            
        calculated_price = base_price
        
        # Appliquer les différents éléments de la formule
        if 'indexation' in formula:
            index_type = formula['indexation'].get('type')
            index_value = formula['indexation'].get('value', 0)
            
            if index_type == 'inflation':
                # Appliquer l'inflation
                years = (reference_date - formula['indexation'].get('base_date', reference_date)).days / 365.25
                calculated_price *= math.pow(1 + index_value / 100, years)
                
            elif index_type == 'reference':
                # Indexer sur un prix de référence
                ref_price = self.PRIX_REFERENCES.get(formula['indexation'].get('reference'), base_price)
                calculated_price = ref_price * (1 + index_value / 100)
                
        # Appliquer la remise
        if 'remise' in formula:
            calculated_price *= (1 - formula['remise'] / 100)
            
        # Appliquer les plafonds
        if 'min_price' in formula:
            calculated_price = max(calculated_price, formula['min_price'])
        if 'max_price' in formula:
            calculated_price = min(calculated_price, formula['max_price'])
            
        return round(calculated_price, 4)
        
    def project_prices(
        self,
        client_id: int,
        years: int,
        inflation_rate: float = 2.0,
        start_date: date = None
    ) -> List[Dict[str, Any]]:
        """Projette les prix futurs pour un client.
        
        Args:
            client_id: ID du client
            years: Nombre d'années à projeter
            inflation_rate: Taux d'inflation annuel (%)
            start_date: Date de début de projection
            
        Returns:
            Liste des projections annuelles
        """
        if start_date is None:
            start_date = date.today()
            
        # Récupérer le prix actuel
        current_price = self.get_active_price(client_id, start_date)
        if not current_price:
            raise ValueError(f"Aucun prix actif pour le client {client_id}")
            
        projections = []
        base_price = current_price.prix_kwh
        
        for year in range(years + 1):
            projection_date = date(start_date.year + year, start_date.month, start_date.day)
            
            # Calculer le prix selon le type de tarif
            if current_price.type_tarif == 'fixe':
                projected_price = base_price
            elif current_price.type_tarif == 'indexe':
                # Appliquer l'inflation
                projected_price = base_price * math.pow(1 + inflation_rate / 100, year)
            elif current_price.type_tarif == 'dynamique' and current_price.formule_calcul:
                projected_price = self.calculate_dynamic_price(
                    base_price,
                    current_price.formule_calcul,
                    projection_date
                )
            else:
                # Par défaut, appliquer l'inflation
                projected_price = base_price * math.pow(1 + inflation_rate / 100, year)
                
            projections.append({
                'annee': projection_date.year,
                'date': projection_date.isoformat(),
                'prix_kwh': round(projected_price, 4),
                'variation_annuelle': 0 if year == 0 else inflation_rate,
                'variation_cumulee': 0 if year == 0 else ((projected_price / base_price - 1) * 100)
            })
            
        return projections
        
    def compare_with_reference(
        self,
        client_id: int,
        reference_type: str = 'EDF_TRV_BASE',
        period_years: int = 1
    ) -> Dict[str, Any]:
        """Compare le prix client avec un prix de référence.
        
        Args:
            client_id: ID du client
            reference_type: Type de prix de référence
            period_years: Période de comparaison en années
            
        Returns:
            Analyse comparative
        """
        # Prix du client
        client_price = self.get_active_price(client_id)
        if not client_price:
            raise ValueError(f"Aucun prix actif pour le client {client_id}")
            
        # Prix de référence
        reference_price = self.PRIX_REFERENCES.get(reference_type, 0.2276)
        
        # Calculs comparatifs
        difference = client_price.prix_kwh - reference_price
        difference_pct = (difference / reference_price) * 100
        
        # Estimation des économies/surcoûts annuels (base 10000 kWh/an)
        conso_estimee = 10000
        economie_annuelle = -difference * conso_estimee
        economie_periode = economie_annuelle * period_years
        
        return {
            'client_prix': client_price.prix_kwh,
            'reference_prix': reference_price,
            'reference_type': reference_type,
            'difference': round(difference, 4),
            'difference_pct': round(difference_pct, 2),
            'economie_annuelle': round(economie_annuelle, 2),
            'economie_periode': round(economie_periode, 2),
            'periode_ans': period_years,
            'avantageux': client_price.prix_kwh < reference_price
        }
        
    def get_zone_default_price(self, zone_name: str) -> Optional[float]:
        """Récupère le prix par défaut d'une zone.
        
        Args:
            zone_name: Nom de la zone
            
        Returns:
            Prix par défaut ou None
        """
        query = """
            SELECT prix_defaut_kwh
            FROM zones_geographiques
            WHERE nom = ? AND actif = TRUE
        """
        
        results = self.db.execute_query(query, (zone_name,))
        
        if results and results[0]['prix_defaut_kwh']:
            return results[0]['prix_defaut_kwh']
        return None
        
    def apply_bulk_price_update(
        self,
        client_ids: List[int],
        prix_kwh: float,
        type_tarif: str = 'fixe',
        date_debut: date = None
    ) -> int:
        """Applique une mise à jour de prix en masse.
        
        Args:
            client_ids: Liste des IDs clients
            prix_kwh: Nouveau prix
            type_tarif: Type de tarif
            date_debut: Date de début (par défaut aujourd'hui)
            
        Returns:
            Nombre de prix créés
        """
        if not client_ids:
            return 0
            
        if date_debut is None:
            date_debut = date.today()
            
        created_count = 0
        
        for client_id in client_ids:
            try:
                # Clôturer le prix actuel si existant
                current = self.get_active_price(client_id, date_debut)
                if current:
                    self._close_price(current.id, date_debut - timedelta(days=1))
                    
                # Créer le nouveau prix
                new_price = PrixClient(
                    id=None,
                    client_id=client_id,
                    prix_kwh=prix_kwh,
                    date_debut=date_debut,
                    date_fin=None,
                    type_tarif=type_tarif,
                    reference_prix=None,
                    remise_pourcentage=0,
                    formule_calcul=None,
                    notes=f"Mise à jour en masse du {date_debut}",
                    date_creation=datetime.now()
                )
                
                self.create_prix(new_price)
                created_count += 1
                
            except Exception as e:
                logger.error(f"Erreur mise à jour prix client {client_id}: {e}")
                
        logger.info(f"Mise à jour en masse: {created_count}/{len(client_ids)} prix créés")
        return created_count
        
    def _validate_prix(self, prix: PrixClient):
        """Valide un prix client.
        
        Args:
            prix: Prix à valider
            
        Raises:
            ValueError: Si validation échoue
        """
        errors = []
        
        # Validation du prix
        if prix.prix_kwh <= 0:
            errors.append("Le prix doit être positif")
        elif prix.prix_kwh > 1:  # 1€/kWh max raisonnable
            errors.append("Le prix semble trop élevé (> 1€/kWh)")
            
        # Validation des dates
        if prix.date_fin and prix.date_fin <= prix.date_debut:
            errors.append("La date de fin doit être après la date de début")
            
        # Validation du type
        types_valides = ['fixe', 'indexe', 'dynamique']
        if prix.type_tarif not in types_valides:
            errors.append(f"Type de tarif invalide. Valides: {', '.join(types_valides)}")
            
        # Validation de la remise
        if prix.remise_pourcentage < 0 or prix.remise_pourcentage > 100:
            errors.append("La remise doit être entre 0 et 100%")
            
        if errors:
            raise ValueError(f"Erreurs de validation: {', '.join(errors)}")
            
    def _check_overlap(self, prix: PrixClient, exclude_id: int = None) -> bool:
        """Vérifie si un prix chevauche avec des périodes existantes.
        
        Args:
            prix: Prix à vérifier
            exclude_id: ID à exclure de la vérification
            
        Returns:
            True si chevauchement détecté
        """
        query = """
            SELECT COUNT(*) as count
            FROM prix_clients
            WHERE client_id = ?
              AND date_debut <= ?
              AND (date_fin IS NULL OR date_fin >= ?)
        """
        
        params = [prix.client_id]
        
        # Date de fin du nouveau prix (ou date très lointaine si NULL)
        new_end = prix.date_fin.isoformat() if prix.date_fin else '9999-12-31'
        params.extend([new_end, prix.date_debut.isoformat()])
        
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
            
        results = self.db.execute_query(query, params)
        return results[0]['count'] > 0
        
    def _close_price(self, prix_id: int, end_date: date):
        """Clôture un prix en définissant sa date de fin.
        
        Args:
            prix_id: ID du prix à clôturer
            end_date: Date de fin
        """
        query = "UPDATE prix_clients SET date_fin = ? WHERE id = ?"
        self.db.execute_command(query, (end_date.isoformat(), prix_id))
        
    def _prix_from_dict(self, data: Dict[str, Any]) -> PrixClient:
        """Crée une instance PrixClient depuis un dictionnaire."""
        # Conversion des dates
        if isinstance(data['date_debut'], str):
            data['date_debut'] = date.fromisoformat(data['date_debut'])
        if data.get('date_fin') and isinstance(data['date_fin'], str):
            data['date_fin'] = date.fromisoformat(data['date_fin'])
        if data.get('date_creation') and isinstance(data['date_creation'], str):
            data['date_creation'] = datetime.fromisoformat(data['date_creation'])
            
        # Conversion de la formule JSON
        if data.get('formule_calcul') and isinstance(data['formule_calcul'], str):
            try:
                data['formule_calcul'] = json.loads(data['formule_calcul'])
            except json.JSONDecodeError:
                data['formule_calcul'] = None
                
        return PrixClient(**data)
    
    def get_average_price(self) -> float:
        """Calcule le prix moyen de tous les clients actifs.
        
        Returns:
            Prix moyen en €/kWh
        """
        try:
            # D'abord, vérifier si la colonne actif existe dans prix_clients
            check_column_query = """
                PRAGMA table_info(prix_clients)
            """
            
            columns = self.db.execute_query(check_column_query)
            has_actif_column = any(col['name'] == 'actif' for col in columns) if columns else False
            
            if has_actif_column:
                query = """
                    SELECT AVG(prix_kwh) as average_price
                    FROM prix_clients pc
                    WHERE pc.actif = TRUE
                    AND (pc.date_fin IS NULL OR pc.date_fin >= DATE('now'))
                """
            else:
                # Si la colonne actif n'existe pas, utiliser seulement les dates
                query = """
                    SELECT AVG(prix_kwh) as average_price
                    FROM prix_clients pc
                    WHERE (pc.date_fin IS NULL OR pc.date_fin >= DATE('now'))
                """
            
            result = self.db.execute_query(query)
            if result and len(result) > 0 and result[0]['average_price'] is not None:
                return float(result[0]['average_price'])
            
            # Si aucun prix trouvé, retourner un prix par défaut
            return self.PRIX_REFERENCES['EDF_TRV_BASE']
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du prix moyen: {e}")
            return self.PRIX_REFERENCES['EDF_TRV_BASE']
    
    def get_price_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques des prix.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        try:
            # Vérifier si la colonne actif existe dans prix_clients
            check_column_query = """
                PRAGMA table_info(prix_clients)
            """
            
            columns = self.db.execute_query(check_column_query)
            has_actif_column = any(col['name'] == 'actif' for col in columns) if columns else False
            
            if has_actif_column:
                query = """
                    SELECT 
                        COUNT(*) as total_prices,
                        MIN(prix_kwh) as min_price,
                        MAX(prix_kwh) as max_price,
                        AVG(prix_kwh) as avg_price,
                        COUNT(DISTINCT client_id) as clients_with_pricing
                    FROM prix_clients
                    WHERE actif = TRUE
                    AND (date_fin IS NULL OR date_fin >= DATE('now'))
                """
            else:
                # Si la colonne actif n'existe pas, utiliser seulement les dates
                query = """
                    SELECT 
                        COUNT(*) as total_prices,
                        MIN(prix_kwh) as min_price,
                        MAX(prix_kwh) as max_price,
                        AVG(prix_kwh) as avg_price,
                        COUNT(DISTINCT client_id) as clients_with_pricing
                    FROM prix_clients
                    WHERE (date_fin IS NULL OR date_fin >= DATE('now'))
                """
            
            result = self.db.execute_query(query)
            
            if result and len(result) > 0:
                stats = result[0]
                return {
                    'total_prices': stats['total_prices'] or 0,
                    'min_price': float(stats['min_price'] or 0),
                    'max_price': float(stats['max_price'] or 0),
                    'avg_price': float(stats['avg_price'] or 0),
                    'clients_with_pricing': stats['clients_with_pricing'] or 0
                }
            
            return {
                'total_prices': 0,
                'min_price': 0.0,
                'max_price': 0.0,
                'avg_price': 0.0,
                'clients_with_pricing': 0
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques de prix: {e}")
            return {
                'total_prices': 0,
                'min_price': 0.0,
                'max_price': 0.0,
                'avg_price': 0.0,
                'clients_with_pricing': 0
            }