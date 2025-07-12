"""Script de migration pour ajouter les tables d'autoconsommation collective."""

import sqlite3
import os
import sys
from datetime import datetime

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def migrate_database():
    """Migre la base de données pour ajouter les nouvelles tables autoconso."""
    
    # Chemin vers la base de données
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../data/erp_clients.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données introuvable: {db_path}")
        print("💡 L'application créera automatiquement les bonnes tables au prochain démarrage.")
        return
    
    print(f"📂 Base de données trouvée: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si les anciennes tables existent
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='points_production'")
        old_table_exists = cursor.fetchone() is not None
        
        if old_table_exists:
            # Vérifier la structure de la table
            cursor.execute("PRAGMA table_info(points_production)")
            columns = {col[1] for col in cursor.fetchall()}
            
            if 'puissance_kwc' in columns and 'capacite_kwc' not in columns:
                print("🔄 Migration nécessaire: ancienne structure détectée")
                
                # Sauvegarder les données existantes si nécessaire
                cursor.execute("SELECT COUNT(*) FROM points_production")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"⚠️  {count} enregistrements trouvés dans l'ancienne table points_production")
                    print("💾 Sauvegarde des données...")
                    
                    # Renommer l'ancienne table
                    cursor.execute("ALTER TABLE points_production RENAME TO points_production_old")
                    print("✅ Ancienne table renommée en points_production_old")
                else:
                    # Supprimer l'ancienne table vide
                    cursor.execute("DROP TABLE IF EXISTS points_production")
                    print("✅ Ancienne table vide supprimée")
        
        # Créer les nouvelles tables
        print("\n📝 Création des nouvelles tables d'autoconsommation...")
        
        # Table Points Production (nouvelle structure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS points_production (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                nom VARCHAR(200) NOT NULL,
                type_installation VARCHAR(50) DEFAULT 'Toiture',
                capacite_kwc REAL NOT NULL,
                capacite_disponible_kwc REAL,
                date_mise_service DATE,
                adresse TEXT,
                latitude REAL,
                longitude REAL,
                actif BOOLEAN DEFAULT TRUE,
                notes TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)
        print("✅ Table points_production créée")
        
        # Table Points Consommation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS points_consommation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                reference_interne VARCHAR(100) NOT NULL,
                type_point VARCHAR(50) DEFAULT 'Principal',
                consommation_annuelle_kwh REAL DEFAULT 0,
                puissance_souscrite_kva INTEGER DEFAULT 36,
                adresse TEXT,
                latitude REAL,
                longitude REAL,
                actif BOOLEAN DEFAULT TRUE,
                notes TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)
        print("✅ Table points_consommation créée")
        
        # Supprimer l'ancienne table autoconso_collective si elle existe
        cursor.execute("DROP TABLE IF EXISTS autoconso_collective")
        
        # Table Autoconsommation Collective (nouvelle structure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS autoconso_collective (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                point_production_id INTEGER NOT NULL,
                point_consommation_id INTEGER NOT NULL,
                pourcentage_allocation REAL NOT NULL CHECK(pourcentage_allocation >= 0 AND pourcentage_allocation <= 100),
                date_debut DATE NOT NULL,
                date_fin DATE,
                actif BOOLEAN DEFAULT TRUE,
                notes TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (point_production_id) REFERENCES points_production(id) ON DELETE CASCADE,
                FOREIGN KEY (point_consommation_id) REFERENCES points_consommation(id) ON DELETE CASCADE
            )
        """)
        print("✅ Table autoconso_collective créée")
        
        # Créer les index
        print("\n🔍 Création des index...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_autoconso_production ON autoconso_collective(point_production_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_autoconso_consommation ON autoconso_collective(point_consommation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_production_client ON points_production(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_points_consommation_client ON points_consommation(client_id)")
        print("✅ Index créés")
        
        # Vérifier si l'ancienne table existe toujours
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='points_production_old'")
        if cursor.fetchone():
            print("\n⚠️  IMPORTANT: L'ancienne table 'points_production_old' a été conservée.")
            print("   Si vous aviez des données, vous devrez les migrer manuellement.")
            print("   Contactez le support si nécessaire.")
        
        conn.commit()
        print("\n✅ Migration terminée avec succès!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erreur lors de la migration: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("🔄 Migration de la base de données ERP pour l'autoconsommation collective")
    print("=" * 60)
    migrate_database()
    print("\n✅ Vous pouvez maintenant relancer l'application OptimPV!")