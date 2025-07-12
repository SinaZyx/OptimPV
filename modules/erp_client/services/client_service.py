"""Service métier pour la gestion des clients.

Ce module fournit toutes les opérations métier liées aux clients,
incluant CRUD, recherche, validation et logique métier.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json

from ..models.client import Client
from ..database.erp_database import ERPDatabase

logger = logging.getLogger(__name__)


class ClientService:
    """Service pour la gestion des clients."""
    
    def __init__(self, db_path: str = None):
        """Initialise le service client.
        
        Args:
            db_path: Chemin vers la base de données (optionnel)
        """
        self.db = ERPDatabase(db_path)
        
    def create_client(self, client: Client) -> Client:
        """Crée un nouveau client.
        
        Args:
            client: Instance de Client à créer
            
        Returns:
            Client créé avec son ID
            
        Raises:
            ValueError: Si validation échoue ou code client existe déjà
        """
        # Validation
        errors = client.validate()
        if errors:
            raise ValueError(f"Erreurs de validation: {', '.join(errors)}")
            
        # Vérifier l'unicité du code client
        if self.get_by_code(client.code_client):
            raise ValueError(f"Le code client '{client.code_client}' existe déjà")
            
        # Préparer les données pour l'insertion
        data = client.to_dict()
        
        # Retirer l'ID pour l'insertion
        data.pop('id', None)
        
        # Créer la requête d'insertion
        columns = list(data.keys())
        placeholders = ['?' for _ in columns]
        query = f"""
            INSERT INTO clients ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        try:
            # Exécuter l'insertion
            client_id = self.db.execute_command(query, tuple(data.values()))
            client.id = client_id
            
            logger.info(f"Client créé: {client.code_client} (ID: {client_id})")
            return client
            
        except Exception as e:
            logger.error(f"Erreur création client: {e}")
            raise
            
    def update_client(self, client: Client) -> Client:
        """Met à jour un client existant.
        
        Args:
            client: Client avec les nouvelles données
            
        Returns:
            Client mis à jour
            
        Raises:
            ValueError: Si client n'existe pas ou validation échoue
        """
        if not client.id:
            raise ValueError("ID client requis pour la mise à jour")
            
        # Vérifier que le client existe
        existing = self.get_by_id(client.id)
        if not existing:
            raise ValueError(f"Client ID {client.id} introuvable")
            
        # Validation
        errors = client.validate()
        if errors:
            raise ValueError(f"Erreurs de validation: {', '.join(errors)}")
            
        # Vérifier l'unicité du code si modifié
        if existing.code_client != client.code_client:
            other = self.get_by_code(client.code_client)
            if other and other.id != client.id:
                raise ValueError(f"Le code client '{client.code_client}' est déjà utilisé")
                
        # Mettre à jour la date de modification
        client.date_modification = datetime.now()
        
        # Préparer les données
        data = client.to_dict()
        data.pop('id')
        data.pop('date_creation', None)
        
        # Créer la requête de mise à jour
        set_clauses = [f"{col} = ?" for col in data.keys()]
        query = f"""
            UPDATE clients
            SET {', '.join(set_clauses)}
            WHERE id = ?
        """
        
        try:
            # Exécuter la mise à jour
            values = list(data.values()) + [client.id]
            self.db.execute_command(query, values)
            
            logger.info(f"Client mis à jour: {client.code_client} (ID: {client.id})")
            return client
            
        except Exception as e:
            logger.error(f"Erreur mise à jour client: {e}")
            raise
            
    def delete_client(self, client_id: int) -> bool:
        """Supprime un client (soft delete).
        
        Args:
            client_id: ID du client à supprimer
            
        Returns:
            True si suppression réussie
        """
        query = "UPDATE clients SET actif = FALSE WHERE id = ?"
        
        try:
            rows = self.db.execute_command(query, (client_id,))
            logger.info(f"Client désactivé: ID {client_id}")
            return rows > 0
            
        except Exception as e:
            logger.error(f"Erreur suppression client: {e}")
            raise
            
    def get_by_id(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID.
        
        Args:
            client_id: ID du client
            
        Returns:
            Client trouvé ou None
        """
        query = "SELECT * FROM clients WHERE id = ?"
        results = self.db.execute_query(query, (client_id,))
        
        if results:
            return Client.from_dict(results[0])
        return None
        
    def get_by_code(self, code_client: str) -> Optional[Client]:
        """Récupère un client par son code.
        
        Args:
            code_client: Code du client
            
        Returns:
            Client trouvé ou None
        """
        query = "SELECT * FROM clients WHERE code_client = ?"
        results = self.db.execute_query(query, (code_client.upper(),))
        
        if results:
            return Client.from_dict(results[0])
        return None
        
    def get_all(self, include_inactive: bool = False) -> List[Client]:
        """Récupère tous les clients.
        
        Args:
            include_inactive: Inclure les clients inactifs
            
        Returns:
            Liste des clients
        """
        query = "SELECT * FROM clients"
        if not include_inactive:
            query += " WHERE actif = TRUE"
        query += " ORDER BY nom"
        
        results = self.db.execute_query(query)
        return [Client.from_dict(row) for row in results]
        
    def search_clients(
        self,
        search_term: str = None,
        type_client: str = None,
        zone_geographique: str = None,
        code_postal: str = None,
        actif_only: bool = True
    ) -> List[Client]:
        """Recherche des clients selon différents critères.
        
        Args:
            search_term: Terme de recherche (nom, code, ville)
            type_client: Filtrer par type
            zone_geographique: Filtrer par zone
            code_postal: Filtrer par code postal
            actif_only: Inclure uniquement les actifs
            
        Returns:
            Liste des clients correspondants
        """
        conditions = []
        params = []
        
        # Condition actif
        if actif_only:
            conditions.append("actif = TRUE")
            
        # Recherche textuelle
        if search_term:
            search_conditions = [
                "nom LIKE ?",
                "code_client LIKE ?",
                "ville LIKE ?",
                "contact_principal LIKE ?"
            ]
            conditions.append(f"({' OR '.join(search_conditions)})")
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern] * 4)
            
        # Filtre type client
        if type_client:
            conditions.append("type_client = ?")
            params.append(type_client)
            
        # Filtre zone
        if zone_geographique:
            conditions.append("zone_geographique = ?")
            params.append(zone_geographique)
            
        # Filtre code postal
        if code_postal:
            if len(code_postal) == 2:  # Département
                conditions.append("code_postal LIKE ?")
                params.append(f"{code_postal}%")
            else:
                conditions.append("code_postal = ?")
                params.append(code_postal)
                
        # Construire la requête
        query = "SELECT * FROM clients"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY nom"
        
        results = self.db.execute_query(query, params)
        return [Client.from_dict(row) for row in results]
        
    def get_clients_by_zone(self, zone: str) -> List[Client]:
        """Récupère tous les clients d'une zone géographique.
        
        Args:
            zone: Nom de la zone
            
        Returns:
            Liste des clients de la zone
        """
        query = """
            SELECT * FROM clients
            WHERE zone_geographique = ? AND actif = TRUE
            ORDER BY nom
        """
        
        results = self.db.execute_query(query, (zone,))
        return [Client.from_dict(row) for row in results]
        
    def get_unique_zones(self) -> List[str]:
        """Récupère la liste des zones géographiques uniques.
        
        Returns:
            Liste des zones géographiques distinctes
        """
        query = """
            SELECT DISTINCT zone_geographique
            FROM clients
            WHERE zone_geographique IS NOT NULL
            AND zone_geographique != ''
            AND actif = TRUE
            ORDER BY zone_geographique
        """
        
        results = self.db.execute_query(query)
        return [row['zone_geographique'] for row in results]
        
    def get_clients_by_type(self, type_client: str) -> List[Client]:
        """Récupère tous les clients d'un type donné.
        
        Args:
            type_client: Type de client
            
        Returns:
            Liste des clients du type
        """
        query = """
            SELECT * FROM clients
            WHERE type_client = ? AND actif = TRUE
            ORDER BY nom
        """
        
        results = self.db.execute_query(query, (type_client,))
        return [Client.from_dict(row) for row in results]
        
    def get_producteurs(self) -> List[Client]:
        """Récupère tous les producteurs (producteur et prosumer)."""
        query = """
            SELECT * FROM clients
            WHERE type_client IN ('producteur', 'prosumer') AND actif = TRUE
            ORDER BY nom
        """
        
        results = self.db.execute_query(query)
        return [Client.from_dict(row) for row in results]
        
    def get_consommateurs(self) -> List[Client]:
        """Récupère tous les consommateurs (consommateur et prosumer)."""
        query = """
            SELECT * FROM clients
            WHERE type_client IN ('consommateur', 'prosumer') AND actif = TRUE
            ORDER BY nom
        """
        
        results = self.db.execute_query(query)
        return [Client.from_dict(row) for row in results]
        
    def geocode_client(self, client: Client) -> Tuple[Optional[float], Optional[float]]:
        """Géocode l'adresse d'un client pour obtenir ses coordonnées GPS.
        
        Args:
            client: Client à géocoder
            
        Returns:
            Tuple (latitude, longitude) ou (None, None) si échec
        """
        if not client.adresse_complete or client.adresse_complete == "Adresse non renseignée":
            return None, None
            
        try:
            # Utiliser geopy pour le géocodage
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut, GeocoderServiceError
            
            geolocator = Nominatim(user_agent="optimpv-erp")
            
            # Construire l'adresse complète pour la recherche
            address = client.adresse_complete
            if client.ville and client.ville not in address:
                address += f", {client.ville}"
            if client.code_postal and client.code_postal not in address:
                address += f", {client.code_postal}"
            address += ", France"  # Ajouter le pays pour plus de précision
            
            try:
                location = geolocator.geocode(address, timeout=10)
                if location:
                    logger.info(f"Géocodage réussi pour {client.code_client}: {location.latitude}, {location.longitude}")
                    return location.latitude, location.longitude
                else:
                    logger.warning(f"Aucun résultat de géocodage pour {client.code_client}")
                    return None, None
                    
            except GeocoderTimedOut:
                logger.error(f"Timeout géocodage pour {client.code_client}")
                return None, None
                
        except Exception as e:
            logger.error(f"Erreur géocodage pour {client.code_client}: {e}")
            return None, None
            
    def update_coordinates(self, client_id: int, latitude: float, longitude: float) -> bool:
        """Met à jour les coordonnées GPS d'un client.
        
        Args:
            client_id: ID du client
            latitude: Nouvelle latitude
            longitude: Nouvelle longitude
            
        Returns:
            True si mise à jour réussie
        """
        query = """
            UPDATE clients
            SET latitude = ?, longitude = ?, date_modification = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        
        try:
            rows = self.db.execute_command(query, (latitude, longitude, client_id))
            logger.info(f"Coordonnées mises à jour pour client ID {client_id}")
            return rows > 0
            
        except Exception as e:
            logger.error(f"Erreur mise à jour coordonnées: {e}")
            raise
            
    def assign_zone_by_postal_code(self, client: Client) -> Optional[str]:
        """Assigne automatiquement une zone géographique selon le code postal.
        
        Args:
            client: Client à assigner
            
        Returns:
            Nom de la zone assignée ou None
        """
        if not client.code_postal:
            return None
            
        # Requête pour trouver la zone correspondante
        query = """
            SELECT zg.nom
            FROM zones_geographiques zg
            JOIN zones_codes_postaux zcp ON zg.id = zcp.zone_id
            WHERE zcp.code_postal = ? AND zg.actif = TRUE
            LIMIT 1
        """
        
        results = self.db.execute_query(query, (client.code_postal,))
        
        if results:
            zone_name = results[0]['nom']
            
            # Mettre à jour le client
            update_query = """
                UPDATE clients
                SET zone_geographique = ?, date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            self.db.execute_command(update_query, (zone_name, client.id))
            logger.info(f"Zone '{zone_name}' assignée au client {client.code_client}")
            
            return zone_name
            
        return None
        
    def get_statistics(self) -> Dict[str, Any]:
        """Calcule des statistiques sur les clients.
        
        Returns:
            Dictionnaire de statistiques
        """
        stats = {
            'total_clients': 0,
            'clients_actifs': 0,
            'par_type': {},
            'par_zone': {},
            'avec_coordonnees': 0,
            'sans_coordonnees': 0
        }
        
        # Total et actifs
        query = "SELECT COUNT(*) as total, SUM(CASE WHEN actif THEN 1 ELSE 0 END) as actifs FROM clients"
        result = self.db.execute_query(query)
        if result:
            stats['total_clients'] = result[0]['total'] or 0
            stats['clients_actifs'] = result[0]['actifs'] or 0
            
        # Par type
        query = """
            SELECT type_client, COUNT(*) as nombre
            FROM clients
            WHERE actif = TRUE
            GROUP BY type_client
        """
        results = self.db.execute_query(query)
        for row in results:
            stats['par_type'][row['type_client']] = row['nombre']
            
        # Par zone
        query = """
            SELECT zone_geographique, COUNT(*) as nombre
            FROM clients
            WHERE actif = TRUE AND zone_geographique IS NOT NULL
            GROUP BY zone_geographique
        """
        results = self.db.execute_query(query)
        for row in results:
            stats['par_zone'][row['zone_geographique']] = row['nombre']
            
        # Avec/sans coordonnées
        query = """
            SELECT 
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as avec_coord,
                SUM(CASE WHEN latitude IS NULL OR longitude IS NULL THEN 1 ELSE 0 END) as sans_coord
            FROM clients
            WHERE actif = TRUE
        """
        result = self.db.execute_query(query)
        if result:
            stats['avec_coordonnees'] = result[0]['avec_coord'] or 0
            stats['sans_coordonnees'] = result[0]['sans_coord'] or 0
            
        return stats
    
    def delete(self, client_id: int) -> bool:
        """Supprime (désactive) un client.
        
        Args:
            client_id: ID du client à supprimer
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Désactiver plutôt que supprimer pour préserver l'intégrité référentielle
            query = """
                UPDATE clients 
                SET actif = FALSE, 
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            
            rows_affected = self.db.execute_command(query, (client_id,))
            
            if rows_affected > 0:
                logger.info(f"Client {client_id} désactivé avec succès")
                return True
            else:
                logger.warning(f"Aucun client trouvé avec l'ID {client_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du client {client_id}: {e}")
            return False
    
    def hard_delete(self, client_id: int) -> bool:
        """Suppression physique d'un client (attention: irréversible).
        
        Args:
            client_id: ID du client à supprimer définitivement
            
        Returns:
            True si succès, False sinon
            
        Warning:
            Cette opération est irréversible et peut affecter l'intégrité référentielle
        """
        try:
            # Vérifier s'il y a des données liées
            linked_tables = [
                'prix_clients',
                'points_production', 
                'points_consommation',
                'autoconso_collective'
            ]
            
            for table in linked_tables:
                query = f"SELECT COUNT(*) as count FROM {table} WHERE client_id = ?"
                result = self.db.execute_query(query, (client_id,))
                if result and result[0]['count'] > 0:
                    logger.warning(f"Client {client_id} a des données liées dans {table}")
                    return False
            
            # Suppression physique
            query = "DELETE FROM clients WHERE id = ?"
            rows_affected = self.db.execute_command(query, (client_id,))
            
            if rows_affected > 0:
                logger.info(f"Client {client_id} supprimé définitivement")
                return True
            else:
                logger.warning(f"Aucun client trouvé avec l'ID {client_id}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la suppression définitive du client {client_id}: {e}")
            return False