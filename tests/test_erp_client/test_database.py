"""Tests pour la base de données ERP.

Ce module teste toutes les opérations de base de données du module ERP,
incluant la création des tables, les migrations et les opérations CRUD.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, date
import sqlite3

from modules.erp_client.database.erp_database import ERPDatabase


class TestERPDatabase:
    """Tests pour la classe ERPDatabase."""
    
    @pytest.fixture
    def temp_db_dir(self):
        """Crée un répertoire temporaire pour les tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def db(self, temp_db_dir):
        """Crée une instance de base de données pour les tests."""
        db_path = os.path.join(temp_db_dir, "test_erp.db")
        return ERPDatabase(db_path)
    
    def test_database_initialization(self, db):
        """Test l'initialisation de la base de données."""
        # Vérifier que le fichier est créé
        assert os.path.exists(db.db_path)
        
        # Vérifier les tables
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            expected_tables = {
                'clients', 'prix_clients', 'points_production',
                'points_consommation', 'autoconso_collective',
                'historique_modifications'
            }
            
            assert expected_tables.issubset(tables)
    
    def test_client_crud_operations(self, db):
        """Test les opérations CRUD sur les clients."""
        # Create
        client_id = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client, adresse, ville, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("CL001", "Test Client", "producteur", "123 rue Test", "TestVille", "test@example.com"))
        
        assert client_id > 0
        
        # Read
        clients = db.execute_query("SELECT * FROM clients WHERE id = ?", (client_id,))
        assert len(clients) == 1
        assert clients[0]['nom'] == "Test Client"
        assert clients[0]['code_client'] == "CL001"
        
        # Update
        rows_affected = db.execute_command(
            "UPDATE clients SET nom = ? WHERE id = ?",
            ("Test Client Updated", client_id)
        )
        assert rows_affected == 1
        
        # Verify update
        updated = db.execute_query("SELECT nom FROM clients WHERE id = ?", (client_id,))
        assert updated[0]['nom'] == "Test Client Updated"
        
        # Delete
        rows_deleted = db.execute_command("DELETE FROM clients WHERE id = ?", (client_id,))
        assert rows_deleted == 1
        
        # Verify deletion
        deleted = db.execute_query("SELECT * FROM clients WHERE id = ?", (client_id,))
        assert len(deleted) == 0
    
    def test_prix_clients_with_foreign_key(self, db):
        """Test les prix clients avec contraintes de clé étrangère."""
        # Créer un client
        client_id = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client)
            VALUES (?, ?, ?)
        """, ("CL002", "Client avec Prix", "consommateur"))
        
        # Ajouter un prix
        prix_id = db.execute_command("""
            INSERT INTO prix_clients (client_id, prix_kwh, date_debut, type_tarif)
            VALUES (?, ?, ?, ?)
        """, (client_id, 0.15, date.today(), "fixe"))
        
        assert prix_id > 0
        
        # Vérifier la cascade de suppression
        db.execute_command("DELETE FROM clients WHERE id = ?", (client_id,))
        
        # Le prix devrait être supprimé aussi
        prix = db.execute_query("SELECT * FROM prix_clients WHERE client_id = ?", (client_id,))
        assert len(prix) == 0
    
    def test_autoconsommation_tables(self, db):
        """Test les tables d'autoconsommation collective."""
        # Créer un client producteur
        prod_id = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client)
            VALUES (?, ?, ?)
        """, ("PROD001", "Producteur Test", "producteur"))
        
        # Créer un client consommateur
        cons_id = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client)
            VALUES (?, ?, ?)
        """, ("CONS001", "Consommateur Test", "consommateur"))
        
        # Créer un point de production
        point_prod_id = db.execute_command("""
            INSERT INTO points_production 
            (client_id, nom, capacite_kwc, capacite_disponible_kwc)
            VALUES (?, ?, ?, ?)
        """, (prod_id, "Toiture Solaire", 100.0, 100.0))
        
        # Créer un point de consommation
        point_cons_id = db.execute_command("""
            INSERT INTO points_consommation 
            (client_id, reference_interne, consommation_annuelle_kwh)
            VALUES (?, ?, ?)
        """, (cons_id, "PDL12345", 50000))
        
        # Créer une allocation
        alloc_id = db.execute_command("""
            INSERT INTO autoconso_collective 
            (point_production_id, point_consommation_id, pourcentage_allocation, date_debut)
            VALUES (?, ?, ?, ?)
        """, (point_prod_id, point_cons_id, 50.0, date.today()))
        
        assert alloc_id > 0
        
        # Vérifier les relations
        allocations = db.execute_query("""
            SELECT ac.*, pp.nom as prod_nom, pc.reference_interne as cons_ref
            FROM autoconso_collective ac
            JOIN points_production pp ON ac.point_production_id = pp.id
            JOIN points_consommation pc ON ac.point_consommation_id = pc.id
            WHERE ac.id = ?
        """, (alloc_id,))
        
        assert len(allocations) == 1
        assert allocations[0]['prod_nom'] == "Toiture Solaire"
        assert allocations[0]['cons_ref'] == "PDL12345"
        assert allocations[0]['pourcentage_allocation'] == 50.0
    
    def test_database_constraints(self, db):
        """Test les contraintes de la base de données."""
        # Test contrainte UNIQUE sur code_client
        db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client)
            VALUES (?, ?, ?)
        """, ("CL003", "Client 1", "producteur"))
        
        with pytest.raises(sqlite3.IntegrityError):
            db.execute_command("""
                INSERT INTO clients (code_client, nom, type_client)
                VALUES (?, ?, ?)
            """, ("CL003", "Client 2", "consommateur"))
        
        # Test contrainte CHECK sur type_client
        with pytest.raises(sqlite3.IntegrityError):
            db.execute_command("""
                INSERT INTO clients (code_client, nom, type_client)
                VALUES (?, ?, ?)
            """, ("CL004", "Client Invalid", "invalid_type"))
        
        # Test contrainte CHECK sur pourcentage_allocation
        client_id = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client)
            VALUES (?, ?, ?)
        """, ("CL005", "Client", "producteur"))
        
        point_id = db.execute_command("""
            INSERT INTO points_production (client_id, nom, capacite_kwc)
            VALUES (?, ?, ?)
        """, (client_id, "Point", 100))
        
        cons_id = db.execute_command("""
            INSERT INTO points_consommation (client_id, reference_interne)
            VALUES (?, ?)
        """, (client_id, "REF001"))
        
        # Pourcentage négatif
        with pytest.raises(sqlite3.IntegrityError):
            db.execute_command("""
                INSERT INTO autoconso_collective 
                (point_production_id, point_consommation_id, pourcentage_allocation, date_debut)
                VALUES (?, ?, ?, ?)
            """, (point_id, cons_id, -10, date.today()))
        
        # Pourcentage > 100
        with pytest.raises(sqlite3.IntegrityError):
            db.execute_command("""
                INSERT INTO autoconso_collective 
                (point_production_id, point_consommation_id, pourcentage_allocation, date_debut)
                VALUES (?, ?, ?, ?)
            """, (point_id, cons_id, 150, date.today()))
    
    def test_database_indexes(self, db):
        """Test la présence des index."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = {row[0] for row in cursor.fetchall()}
            
            expected_indexes = {
                'idx_clients_code',
                'idx_clients_zone',
                'idx_prix_client_date',
                'idx_autoconso_production',
                'idx_autoconso_consommation',
                'idx_points_production_client',
                'idx_points_consommation_client'
            }
            
            assert expected_indexes.issubset(indexes)
    
    def test_historique_modifications(self, db):
        """Test l'historique des modifications."""
        # Créer un enregistrement d'historique
        hist_id = db.execute_command("""
            INSERT INTO historique_modifications 
            (table_name, record_id, action, old_values, new_values, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("clients", 1, "UPDATE", '{"nom": "Ancien"}', '{"nom": "Nouveau"}', "user123"))
        
        assert hist_id > 0
        
        # Vérifier l'historique
        history = db.execute_query("""
            SELECT * FROM historique_modifications WHERE id = ?
        """, (hist_id,))
        
        assert len(history) == 1
        assert history[0]['table_name'] == "clients"
        assert history[0]['action'] == "UPDATE"
    
    def test_get_database_stats(self, db):
        """Test les statistiques de la base de données."""
        # Ajouter quelques données
        for i in range(5):
            db.execute_command("""
                INSERT INTO clients (code_client, nom, type_client)
                VALUES (?, ?, ?)
            """, (f"CL00{i}", f"Client {i}", "producteur"))
        
        stats = db.get_database_stats()
        
        assert stats['clients'] == 5
        assert stats['prix_clients'] == 0
        assert stats['points_production'] == 0
        assert stats['autoconso_collective'] == 0
    
    def test_backup_database(self, db, temp_db_dir):
        """Test la sauvegarde de la base de données."""
        # Ajouter des données
        db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client)
            VALUES (?, ?, ?)
        """, ("CL001", "Client Test", "producteur"))
        
        # Créer une sauvegarde
        backup_path = db.backup_database(backup_dir=temp_db_dir)
        
        assert os.path.exists(backup_path)
        assert "erp_clients_backup_" in backup_path
        
        # Vérifier que la sauvegarde contient les données
        backup_conn = sqlite3.connect(backup_path)
        cursor = backup_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clients")
        count = cursor.fetchone()[0]
        backup_conn.close()
        
        assert count == 1
    
    def test_transaction_rollback(self, db):
        """Test le rollback des transactions."""
        # Compter les clients avant
        before = db.execute_query("SELECT COUNT(*) as count FROM clients")[0]['count']
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                # Insérer un client
                cursor.execute("""
                    INSERT INTO clients (code_client, nom, type_client)
                    VALUES (?, ?, ?)
                """, ("CL999", "Client Transaction", "producteur"))
                
                # Forcer une erreur
                raise Exception("Test rollback")
        except:
            pass
        
        # Vérifier que le client n'a pas été ajouté
        after = db.execute_query("SELECT COUNT(*) as count FROM clients")[0]['count']
        assert before == after
    
    def test_complex_queries(self, db):
        """Test des requêtes complexes."""
        # Créer des données de test
        prod_id = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client, zone_geographique)
            VALUES (?, ?, ?, ?)
        """, ("PROD001", "Producteur Sud", "producteur", "Sud"))
        
        cons_id1 = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client, zone_geographique)
            VALUES (?, ?, ?, ?)
        """, ("CONS001", "Consommateur 1", "consommateur", "Sud"))
        
        cons_id2 = db.execute_command("""
            INSERT INTO clients (code_client, nom, type_client, zone_geographique)
            VALUES (?, ?, ?, ?)
        """, ("CONS002", "Consommateur 2", "consommateur", "Nord"))
        
        # Test requête avec JOIN et agrégation
        results = db.execute_query("""
            SELECT 
                zone_geographique,
                type_client,
                COUNT(*) as count
            FROM clients
            GROUP BY zone_geographique, type_client
            ORDER BY zone_geographique, type_client
        """)
        
        assert len(results) == 3
        
        # Vérifier les résultats
        zone_counts = {(r['zone_geographique'], r['type_client']): r['count'] for r in results}
        assert zone_counts[('Sud', 'producteur')] == 1
        assert zone_counts[('Sud', 'consommateur')] == 1
        assert zone_counts[('Nord', 'consommateur')] == 1