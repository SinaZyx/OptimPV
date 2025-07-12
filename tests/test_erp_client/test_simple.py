"""Test simple du module ERP pour vérification rapide."""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import tempfile
import shutil
from datetime import date

from modules.erp_client.database.erp_database import ERPDatabase
from modules.erp_client.services.client_service import ClientService
from modules.erp_client.services.pricing_service import PricingService
from modules.erp_client.services.capacity_service import CapacityService
from modules.erp_client.models.client import Client, TypeClient
from modules.erp_client.models.pricing import PrixClient, TypeTarif
from modules.erp_client.models.autoconso import PointProduction, PointConsommation, AutoconsoCollective


def test_module_erp():
    """Test simple du module ERP."""
    print("🧪 TEST DU MODULE ERP CLIENT")
    print("=" * 60)
    
    # Créer un répertoire temporaire
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Répertoire temporaire: {temp_dir}")
    
    try:
        # 1. Test de la base de données
        print("\n1️⃣ Test de la base de données...")
        db_path = os.path.join(temp_dir, "test_erp.db")
        db = ERPDatabase(db_path)
        print("✅ Base de données créée")
        
        # 2. Test des services
        print("\n2️⃣ Test des services...")
        client_service = ClientService(db)
        pricing_service = PricingService(db)
        capacity_service = CapacityService(db)
        print("✅ Services initialisés")
        
        # 3. Test création client
        print("\n3️⃣ Test création client...")
        client = Client(
            code_client="test001",
            nom="Client Test",
            type_client=TypeClient.PRODUCTEUR,
            email="test@example.com",
            ville="Nice"
        )
        created_client = client_service.create(client)
        assert created_client.id is not None
        assert created_client.code_client == "TEST001"
        print(f"✅ Client créé: {created_client.nom} (ID: {created_client.id})")
        
        # 4. Test création prix
        print("\n4️⃣ Test création prix...")
        prix = PrixClient(
            client_id=created_client.id,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE
        )
        created_prix = pricing_service.create(prix)
        assert created_prix.id is not None
        print(f"✅ Prix créé: {created_prix.prix_kwh}€/kWh")
        
        # 5. Test création point de production
        print("\n5️⃣ Test création point de production...")
        point_prod = PointProduction(
            client_id=created_client.id,
            nom="Production Test",
            capacite_kwc=100.0
        )
        created_prod = capacity_service.create_production_point(point_prod)
        assert created_prod.id is not None
        print(f"✅ Point de production créé: {created_prod.capacite_kwc} kWc")
        
        # 6. Test recherche
        print("\n6️⃣ Test recherche client...")
        found_clients = client_service.search("Test")
        assert len(found_clients) == 1
        print(f"✅ Client trouvé par recherche")
        
        # 7. Test statistiques
        print("\n7️⃣ Test statistiques...")
        stats = client_service.get_statistics()
        assert stats['total_clients'] == 1
        assert stats['producteurs'] == 1
        print(f"✅ Statistiques: {stats}")
        
        # 8. Test suppression
        print("\n8️⃣ Test suppression...")
        deleted = client_service.delete(created_client.id)
        assert deleted is True
        assert client_service.get_by_id(created_client.id) is None
        print("✅ Client supprimé")
        
        print("\n✅ TOUS LES TESTS SONT PASSÉS!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Nettoyer
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Répertoire temporaire supprimé")


if __name__ == "__main__":
    success = test_module_erp()
    exit(0 if success else 1)