"""Script pour initialiser des données de démonstration dans le module ERP."""

from datetime import date, datetime
from models.client import Client
from services.client_service import ClientService
from services.pricing_service import PricingService, PrixClient

def init_demo_data():
    """Initialise quelques clients de démonstration."""
    
    client_service = ClientService()
    pricing_service = PricingService()
    
    # Données de démonstration
    demo_clients = [
        {
            'code_client': 'DEMO001',
            'nom': 'Soleil Azur SARL',
            'type_client': 'producteur',
            'adresse': '15 Avenue des Fleurs',
            'code_postal': '06000',
            'ville': 'Nice',
            'zone_geographique': 'Nice Centre',
            'telephone': '04 93 00 00 01',
            'email': 'contact@soleilazur.fr',
            'siret': '12345678901234',
            'contact_principal': 'Jean Dupont'
        },
        {
            'code_client': 'DEMO002',
            'nom': 'Boulangerie du Port',
            'type_client': 'consommateur',
            'adresse': '8 Rue du Port',
            'code_postal': '06300',
            'ville': 'Nice',
            'zone_geographique': 'Nice Port',
            'telephone': '04 93 00 00 02',
            'email': 'boulangerie@port.fr'
        },
        {
            'code_client': 'DEMO003',
            'nom': 'Hôtel Vista Mare',
            'type_client': 'prosumer',
            'adresse': '120 Promenade des Anglais',
            'code_postal': '06000',
            'ville': 'Nice',
            'zone_geographique': 'Nice Promenade',
            'telephone': '04 93 00 00 03',
            'email': 'info@vistamare.fr',
            'siret': '98765432109876'
        }
    ]
    
    created_count = 0
    
    for client_data in demo_clients:
        try:
            # Vérifier si le client existe déjà
            existing = client_service.get_by_code(client_data['code_client'])
            if existing:
                print(f"Client {client_data['code_client']} existe déjà")
                continue
                
            # Créer le client
            client = Client(**client_data)
            created_client = client_service.create_client(client)
            print(f"✅ Client créé: {created_client.nom}")
            
            # Créer un prix pour le client
            prix = PrixClient(
                id=None,
                client_id=created_client.id,
                prix_kwh=0.15 if created_client.type_client == 'producteur' else 0.18,
                date_debut=date.today(),
                date_fin=None,
                type_tarif='fixe',
                reference_prix='EDF_TRV_BASE',
                remise_pourcentage=5.0 if created_client.type_client == 'prosumer' else 0,
                formule_calcul=None,
                notes='Prix de démonstration',
                date_creation=None
            )
            
            pricing_service.create_prix(prix)
            print(f"   Prix défini: {prix.prix_kwh} €/kWh")
            
            created_count += 1
            
        except Exception as e:
            print(f"❌ Erreur création client {client_data['code_client']}: {e}")
            
    print(f"\n{created_count} clients de démonstration créés.")
    

if __name__ == '__main__':
    init_demo_data()