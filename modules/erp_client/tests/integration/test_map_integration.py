"""Script de test pour vérifier l'intégration cartographique ERP."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from modules.erp_client.services.client_service import ClientService

def test_map_integration():
    """Teste l'intégration avec le module de cartographie."""
    
    print("🗺️ Test d'intégration cartographique ERP")
    print("=" * 50)
    
    # Initialiser le service
    client_service = ClientService()
    
    # Récupérer tous les clients
    all_clients = client_service.get_all(include_inactive=False)
    print(f"\n📊 Total clients actifs: {len(all_clients)}")
    
    # Filtrer les clients avec coordonnées
    clients_with_coords = [
        client for client in all_clients
        if client.latitude is not None and client.longitude is not None
    ]
    
    print(f"📍 Clients avec coordonnées GPS: {len(clients_with_coords)}")
    
    # Afficher les détails par type
    by_type = {
        'producteur': [],
        'consommateur': [],
        'prosumer': []
    }
    
    for client in clients_with_coords:
        if client.type_client in by_type:
            by_type[client.type_client].append(client)
    
    print("\n🏭 Répartition par type:")
    for type_client, clients in by_type.items():
        print(f"  - {type_client}: {len(clients)} clients")
        for client in clients[:3]:  # Afficher max 3 exemples
            print(f"    • {client.nom} ({client.ville}) - {client.latitude:.4f}, {client.longitude:.4f}")
    
    # Vérifier les zones géographiques
    zones = {}
    for client in clients_with_coords:
        zone = client.zone_geographique or "Non définie"
        if zone not in zones:
            zones[zone] = 0
        zones[zone] += 1
    
    print("\n🗺️ Répartition par zone:")
    for zone, count in sorted(zones.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {zone}: {count} clients")
    
    # Instructions pour l'utilisateur
    print("\n✅ Test terminé!")
    print("\n📝 Pour visualiser ces clients sur la carte:")
    print("1. Lancer l'application OptimPV")
    print("2. Aller dans 'ERP Clients' → onglet 'Cartographie'")
    print("3. Cocher 'Afficher les clients ERP'")
    print("4. La carte affichera les clients avec des marqueurs colorés:")
    print("   - 🟢 Vert = Producteurs")
    print("   - 🔴 Rouge = Consommateurs")
    print("   - 🔵 Bleu = Prosumers")
    
    return len(clients_with_coords) > 0

if __name__ == '__main__':
    success = test_map_integration()
    exit(0 if success else 1)