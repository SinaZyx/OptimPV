"""Script pour initialiser des données de démonstration avec coordonnées GPS."""

from datetime import date
from models.client import Client
from services.client_service import ClientService
from services.pricing_service import PricingService, PrixClient

def init_demo_data_with_coords():
    """Initialise des clients de démonstration avec coordonnées GPS."""
    
    client_service = ClientService()
    pricing_service = PricingService()
    
    # Données de démonstration avec coordonnées GPS (région de Nice/Cannes)
    demo_clients = [
        {
            'code_client': 'PROD001',
            'nom': 'Centrale Solaire Nice Ouest',
            'type_client': 'producteur',
            'adresse': '250 Route de Grenoble',
            'code_postal': '06200',
            'ville': 'Nice',
            'zone_geographique': 'Nice Ouest',
            'telephone': '04 93 00 11 11',
            'email': 'contact@solaire-nice.fr',
            'siret': '12345678901234',
            'latitude': 43.6758,
            'longitude': 7.1998,
            'contact_principal': 'Marie Soleil',
            'notes': 'Installation 500 kWc sur toiture'
        },
        {
            'code_client': 'CONS001',
            'nom': 'Supermarché Bio Cannes',
            'type_client': 'consommateur',
            'adresse': '45 Boulevard Carnot',
            'code_postal': '06400',
            'ville': 'Cannes',
            'zone_geographique': 'Cannes Centre',
            'telephone': '04 93 00 22 22',
            'email': 'direction@bio-cannes.fr',
            'latitude': 43.5528,
            'longitude': 7.0174,
            'notes': 'Consommation importante, intéressé par autoconso'
        },
        {
            'code_client': 'PROS001',
            'nom': 'Hôtel Baie des Anges',
            'type_client': 'prosumer',
            'adresse': '770 Promenade des Anglais',
            'code_postal': '06000',
            'ville': 'Nice',
            'zone_geographique': 'Nice Promenade',
            'telephone': '04 93 00 33 33',
            'email': 'info@hotel-baie.fr',
            'siret': '98765432109876',
            'latitude': 43.6942,
            'longitude': 7.2663,
            'contact_principal': 'Pierre Durand',
            'notes': 'Installation PV 200 kWc + consommation hôtelière'
        },
        {
            'code_client': 'PROD002',
            'nom': 'Toitures Solaires Antibes',
            'type_client': 'producteur',
            'adresse': '2300 Route de Grasse',
            'code_postal': '06600',
            'ville': 'Antibes',
            'zone_geographique': 'Antibes',
            'telephone': '04 93 00 44 44',
            'email': 'contact@toitures-antibes.fr',
            'latitude': 43.5808,
            'longitude': 7.1239,
            'notes': 'Plusieurs sites de production'
        },
        {
            'code_client': 'CONS002',
            'nom': 'Centre Commercial Cap 3000',
            'type_client': 'consommateur',
            'adresse': '319 Avenue Eugène Donadeï',
            'code_postal': '06700',
            'ville': 'Saint-Laurent-du-Var',
            'zone_geographique': 'Saint-Laurent',
            'telephone': '04 93 00 55 55',
            'email': 'direction@cap3000.fr',
            'latitude': 43.6654,
            'longitude': 7.1885,
            'notes': 'Très forte consommation, potentiel énorme'
        },
        {
            'code_client': 'PROS002',
            'nom': 'Clinique Saint-Antoine',
            'type_client': 'prosumer',
            'adresse': '25 Avenue de la Californie',
            'code_postal': '06400',
            'ville': 'Cannes',
            'zone_geographique': 'Cannes Californie',
            'telephone': '04 93 00 66 66',
            'email': 'admin@clinique-stantoine.fr',
            'latitude': 43.5457,
            'longitude': 7.0356,
            'notes': 'Panneaux sur parking + consommation 24/7'
        },
        {
            'code_client': 'PROD003',
            'nom': 'Ferme Solaire Mougins',
            'type_client': 'producteur',
            'adresse': '1255 Avenue de Tournamy',
            'code_postal': '06250',
            'ville': 'Mougins',
            'zone_geographique': 'Mougins',
            'telephone': '04 93 00 77 77',
            'email': 'contact@ferme-mougins.fr',
            'latitude': 43.5997,
            'longitude': 7.0058,
            'siret': '11223344556677',
            'contact_principal': 'Jean Vert',
            'notes': 'Installation agrivoltaïque 1 MWc'
        },
        {
            'code_client': 'CONS003',
            'nom': 'Zone Industrielle Carros',
            'type_client': 'consommateur',
            'adresse': '1ère Avenue',
            'code_postal': '06510',
            'ville': 'Carros',
            'zone_geographique': 'Carros',
            'telephone': '04 93 00 88 88',
            'email': 'contact@zi-carros.fr',
            'latitude': 43.7917,
            'longitude': 7.1875,
            'notes': 'Plusieurs entreprises intéressées'
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
            print(f"✅ Client créé: {created_client.nom} ({created_client.type_client})")
            print(f"   📍 Coordonnées: {created_client.latitude}, {created_client.longitude}")
            
            # Créer un prix pour le client
            if created_client.type_client == 'producteur':
                prix_kwh = 0.12  # Prix de vente pour producteur
            elif created_client.type_client == 'consommateur':
                prix_kwh = 0.18  # Prix d'achat pour consommateur
            else:  # prosumer
                prix_kwh = 0.15  # Prix intermédiaire
                
            prix = PrixClient(
                id=None,
                client_id=created_client.id,
                prix_kwh=prix_kwh,
                date_debut=date.today(),
                date_fin=None,
                type_tarif='fixe',
                reference_prix='DEMO_2024',
                remise_pourcentage=5.0 if created_client.type_client == 'prosumer' else 0,
                formule_calcul=None,
                notes=f'Prix de démonstration {created_client.type_client}',
                date_creation=None
            )
            
            pricing_service.create_prix(prix)
            print(f"   💰 Prix défini: {prix.prix_kwh} €/kWh")
            
            created_count += 1
            
        except Exception as e:
            print(f"❌ Erreur création client {client_data['code_client']}: {e}")
            
    print(f"\n✅ {created_count} clients de démonstration créés avec coordonnées GPS.")
    print("\n📍 Ces clients sont maintenant visibles sur la carte de prospection!")
    

if __name__ == '__main__':
    init_demo_data_with_coords()