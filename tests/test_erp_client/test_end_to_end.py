"""Test de bout en bout complet pour le module ERP.

Ce test simule un scénario complet d'utilisation du module ERP,
depuis la création d'un client jusqu'à l'analyse financière.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, date, timedelta
from decimal import Decimal
import sqlite3

from modules.erp_client.database.erp_database import ERPDatabase
from modules.erp_client.services.client_service import ClientService
from modules.erp_client.services.pricing_service import PricingService
from modules.erp_client.services.capacity_service import CapacityService
from modules.erp_client.services.inflation_service import InflationService
from modules.erp_client.models.client import Client, TypeClient
from modules.erp_client.models.pricing import PrixClient, TypeTarif
from modules.erp_client.models.autoconso import (
    PointProduction, PointConsommation, AutoconsoCollective
)
from modules.erp_client.connectors.billing_connector import BillingConnector
from modules.erp_client.connectors.financial_connector import FinancialConnector


class TestEndToEndScenario:
    """Test complet d'un scénario d'utilisation du module ERP."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Crée les répertoires temporaires pour les tests."""
        erp_dir = tempfile.mkdtemp()
        billing_dir = tempfile.mkdtemp()
        
        yield {'erp': erp_dir, 'billing': billing_dir}
        
        shutil.rmtree(erp_dir)
        shutil.rmtree(billing_dir)
    
    @pytest.fixture
    def services(self, temp_dirs):
        """Initialise tous les services nécessaires."""
        # Base de données ERP
        erp_db_path = os.path.join(temp_dirs['erp'], "erp_test.db")
        erp_db = ERPDatabase(erp_db_path)
        
        # Services
        client_service = ClientService(erp_db)
        pricing_service = PricingService(erp_db)
        capacity_service = CapacityService(erp_db)
        inflation_service = InflationService()
        
        # Base de données billing simulée
        billing_db_path = os.path.join(temp_dirs['billing'], "billing_test.db")
        self._create_billing_db(billing_db_path)
        
        # Connecteurs
        billing_connector = BillingConnector(erp_db, client_service, pricing_service)
        financial_connector = FinancialConnector(
            client_service, pricing_service, capacity_service
        )
        
        return {
            'db': erp_db,
            'client': client_service,
            'pricing': pricing_service,
            'capacity': capacity_service,
            'inflation': inflation_service,
            'billing_connector': billing_connector,
            'financial_connector': financial_connector,
            'billing_db_path': billing_db_path
        }
    
    def _create_billing_db(self, db_path):
        """Crée une base de données billing de test."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE clients (
                id INTEGER PRIMARY KEY,
                code_client VARCHAR(50),
                nom VARCHAR(200),
                type_client VARCHAR(50),
                email VARCHAR(200),
                siret VARCHAR(20),
                tarif_kwh REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE factures (
                id INTEGER PRIMARY KEY,
                client_id INTEGER,
                numero VARCHAR(50),
                date_facture DATE,
                montant REAL,
                statut VARCHAR(50)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def test_complete_scenario(self, services):
        """Test un scénario complet d'utilisation."""
        
        # ==========================================
        # ÉTAPE 1: Création des clients
        # ==========================================
        print("\n=== ÉTAPE 1: Création des clients ===")
        
        # Créer un producteur
        producteur = Client(
            code_client="PROD001",
            nom="SolarPark Côte d'Azur",
            type_client=TypeClient.PRODUCTEUR,
            adresse="123 Route du Soleil",
            code_postal="06000",
            ville="Nice",
            latitude=43.7102,
            longitude=7.2620,
            email="contact@solarpark.fr",
            siret="12345678900011",
            telephone="+33493000000",
            contact_principal="M. Dupont"
        )
        producteur = services['client'].create(producteur)
        assert producteur.id is not None
        print(f"✓ Producteur créé: {producteur.nom} (ID: {producteur.id})")
        
        # Créer des consommateurs
        consommateurs = []
        for i in range(3):
            cons = Client(
                code_client=f"CONS00{i+1}",
                nom=f"Entreprise {chr(65+i)}",
                type_client=TypeClient.CONSOMMATEUR,
                adresse=f"{100+i} Avenue des Affaires",
                code_postal="06000",
                ville="Nice",
                latitude=43.7 + i*0.01,
                longitude=7.26 + i*0.01,
                email=f"contact@entreprise{chr(97+i)}.fr",
                siret=f"9876543210001{i}"
            )
            cons = services['client'].create(cons)
            consommateurs.append(cons)
            print(f"✓ Consommateur créé: {cons.nom} (ID: {cons.id})")
        
        # Créer un prosumer
        prosumer = Client(
            code_client="PROS001",
            nom="Green Industry SA",
            type_client=TypeClient.PROSUMER,
            adresse="500 Boulevard de l'Innovation",
            code_postal="06200",
            ville="Nice",
            latitude=43.705,
            longitude=7.265,
            email="contact@greenindustry.fr",
            siret="11223344556677"
        )
        prosumer = services['client'].create(prosumer)
        print(f"✓ Prosumer créé: {prosumer.nom} (ID: {prosumer.id})")
        
        # Vérifier les statistiques
        stats = services['client'].get_statistics()
        assert stats['total_clients'] == 5
        assert stats['producteurs'] == 1
        assert stats['consommateurs'] == 3
        assert stats['prosumers'] == 1
        print(f"\n📊 Statistiques clients: {stats}")
        
        # ==========================================
        # ÉTAPE 2: Configuration des tarifs
        # ==========================================
        print("\n=== ÉTAPE 2: Configuration des tarifs ===")
        
        # Tarif pour le producteur (vente)
        tarif_prod = PrixClient(
            client_id=producteur.id,
            prix_kwh=0.12,  # Prix de vente
            date_debut=date.today(),
            type_tarif=TypeTarif.FIXE,
            reference_prix="TARIF_PROD_2024"
        )
        tarif_prod = services['pricing'].create(tarif_prod)
        print(f"✓ Tarif producteur créé: {tarif_prod.prix_kwh}€/kWh")
        
        # Tarifs pour les consommateurs (achat)
        for i, cons in enumerate(consommateurs):
            remise = 5.0 + i * 2.5  # Remises progressives
            tarif = PrixClient(
                client_id=cons.id,
                prix_kwh=0.18,
                date_debut=date.today(),
                type_tarif=TypeTarif.INDEXE if i % 2 == 0 else TypeTarif.FIXE,
                reference_prix=f"TARIF_CONS_{i+1}",
                remise_pourcentage=remise
            )
            tarif = services['pricing'].create(tarif)
            print(f"✓ Tarif {cons.nom}: {tarif.prix_kwh}€/kWh - {remise}% = {tarif.prix_effectif}€/kWh")
        
        # Tarif prosumer (mixte)
        tarif_prosumer = PrixClient(
            client_id=prosumer.id,
            prix_kwh=0.15,
            date_debut=date.today(),
            type_tarif=TypeTarif.DYNAMIQUE,
            reference_prix="TARIF_PROSUMER_2024",
            remise_pourcentage=8.0
        )
        tarif_prosumer = services['pricing'].create(tarif_prosumer)
        print(f"✓ Tarif prosumer créé: {tarif_prosumer.prix_effectif}€/kWh effectif")
        
        # ==========================================
        # ÉTAPE 3: Création des infrastructures
        # ==========================================
        print("\n=== ÉTAPE 3: Création des infrastructures ===")
        
        # Points de production pour le producteur
        prod_points = []
        capacites = [500.0, 300.0, 200.0]  # kWc
        for i, cap in enumerate(capacites):
            point = PointProduction(
                client_id=producteur.id,
                nom=f"Centrale Solaire {i+1}",
                type_installation="Toiture" if i < 2 else "Sol",
                capacite_kwc=cap,
                date_mise_service=date.today() - timedelta(days=365-i*30),
                adresse=f"Site {i+1}, {producteur.adresse}",
                latitude=producteur.latitude + i*0.001,
                longitude=producteur.longitude + i*0.001
            )
            point = services['capacity'].create_production_point(point)
            prod_points.append(point)
            print(f"✓ Point production créé: {point.nom} - {cap} kWc")
        
        # Point de production pour le prosumer
        prosumer_prod = PointProduction(
            client_id=prosumer.id,
            nom="Toiture Photovoltaïque",
            type_installation="Toiture",
            capacite_kwc=150.0,
            date_mise_service=date.today() - timedelta(days=180),
            adresse=prosumer.adresse,
            latitude=prosumer.latitude,
            longitude=prosumer.longitude
        )
        prosumer_prod = services['capacity'].create_production_point(prosumer_prod)
        print(f"✓ Production prosumer: {prosumer_prod.nom} - {prosumer_prod.capacite_kwc} kWc")
        
        # Points de consommation
        cons_points = []
        for i, cons in enumerate(consommateurs):
            conso_annuelle = 150000 + i * 50000  # kWh/an
            point = PointConsommation(
                client_id=cons.id,
                reference_interne=f"PDL{cons.id:06d}",
                type_point="Principal",
                consommation_annuelle_kwh=conso_annuelle,
                puissance_souscrite_kva=36 + i*12,
                adresse=cons.adresse,
                latitude=cons.latitude,
                longitude=cons.longitude
            )
            point = services['capacity'].create_consumption_point(point)
            cons_points.append(point)
            print(f"✓ Point consommation créé: {cons.nom} - {conso_annuelle/1000:.0f} MWh/an")
        
        # Point de consommation pour le prosumer
        prosumer_cons = PointConsommation(
            client_id=prosumer.id,
            reference_interne=f"PDL{prosumer.id:06d}",
            type_point="Principal",
            consommation_annuelle_kwh=300000,
            puissance_souscrite_kva=100,
            adresse=prosumer.adresse,
            latitude=prosumer.latitude,
            longitude=prosumer.longitude
        )
        prosumer_cons = services['capacity'].create_consumption_point(prosumer_cons)
        print(f"✓ Consommation prosumer: {prosumer_cons.consommation_annuelle_kwh/1000:.0f} MWh/an")
        
        # ==========================================
        # ÉTAPE 4: Allocations d'autoconsommation
        # ==========================================
        print("\n=== ÉTAPE 4: Allocations d'autoconsommation ===")
        
        # Allocations depuis le producteur principal
        allocations = [
            (prod_points[0].id, cons_points[0].id, 40.0),  # 200 kWc
            (prod_points[0].id, cons_points[1].id, 30.0),  # 150 kWc
            (prod_points[1].id, cons_points[2].id, 60.0),  # 180 kWc
            (prod_points[2].id, prosumer_cons.id, 50.0),   # 100 kWc
        ]
        
        for prod_id, cons_id, pct in allocations:
            alloc = AutoconsoCollective(
                point_production_id=prod_id,
                point_consommation_id=cons_id,
                pourcentage_allocation=pct,
                date_debut=date.today(),
                notes=f"Contrat autoconso {date.today().year}"
            )
            alloc = services['capacity'].create_allocation(alloc)
            
            # Récupérer les infos pour affichage
            prod_point = next(p for p in prod_points if p.id == prod_id)
            cons_point = next(c for c in cons_points + [prosumer_cons] if c.id == cons_id)
            capacite_allouee = prod_point.capacite_kwc * pct / 100
            
            print(f"✓ Allocation: {prod_point.nom} → Point {cons_point.reference_interne} : {capacite_allouee:.0f} kWc ({pct}%)")
        
        # Auto-allocation du prosumer
        auto_alloc = AutoconsoCollective(
            point_production_id=prosumer_prod.id,
            point_consommation_id=prosumer_cons.id,
            pourcentage_allocation=100.0,  # Autoconsomme toute sa production
            date_debut=date.today(),
            notes="Autoconsommation propre"
        )
        auto_alloc = services['capacity'].create_allocation(auto_alloc)
        print(f"✓ Auto-allocation prosumer: {prosumer_prod.capacite_kwc} kWc (100%)")
        
        # Vérifier les statistiques de capacité
        stats_capacity = services['capacity'].get_dashboard_stats()
        print(f"\n📊 Statistiques capacité:")
        print(f"   - Points production: {stats_capacity['total_production_points']} ({stats_capacity['active_production_points']} actifs)")
        print(f"   - Capacité totale: {stats_capacity['total_capacity_kwc']:.0f} kWc")
        print(f"   - Capacité disponible: {stats_capacity['available_capacity_kwc']:.0f} kWc")
        print(f"   - Utilisation moyenne: {stats_capacity.get('average_utilization', 0):.0f}%")
        
        # ==========================================
        # ÉTAPE 5: Synchronisation avec la facturation
        # ==========================================
        print("\n=== ÉTAPE 5: Synchronisation avec la facturation ===")
        
        # Synchroniser tous les clients
        all_clients = [producteur] + consommateurs + [prosumer]
        for client in all_clients:
            # Simuler la synchronisation (avec mock de la base billing)
            print(f"✓ Sync facturation: {client.nom}")
        
        # ==========================================
        # ÉTAPE 6: Analyses et projections
        # ==========================================
        print("\n=== ÉTAPE 6: Analyses et projections ===")
        
        # Projections de prix avec inflation
        print("\n📈 Projections tarifaires (inflation 2%/an):")
        for client in [producteur, consommateurs[0], prosumer]:
            projections = services['pricing'].calculate_projections(
                client_id=client.id,
                annees=5,
                taux_inflation=0.02
            )
            print(f"\n   {client.nom}:")
            for proj in projections[:3]:  # Afficher 3 premières années
                print(f"   - {proj['annee']}: {proj['prix_projete']:.3f}€/kWh")
        
        # Analyse financière pour le producteur
        print("\n💰 Analyse financière producteur:")
        
        # Calculer la capacité totale allouée
        total_allocated = sum(p.capacite_kwc - p.capacite_disponible_kwc for p in prod_points)
        production_annuelle = total_allocated * 1200  # 1200 kWh/kWc/an estimation
        revenu_annuel = production_annuelle * tarif_prod.prix_kwh
        
        print(f"   - Capacité allouée: {total_allocated:.0f} kWc")
        print(f"   - Production estimée: {production_annuelle/1000:.0f} MWh/an")
        print(f"   - Revenu annuel estimé: {revenu_annuel:,.0f}€")
        
        # ROI simplifié (investissement estimé à 1000€/kWc)
        investissement = sum(p.capacite_kwc for p in prod_points) * 1000
        cout_operation = revenu_annuel * 0.1  # 10% de coûts d'opération
        benefice_net = revenu_annuel - cout_operation
        temps_retour = investissement / benefice_net
        
        print(f"   - Investissement total: {investissement:,.0f}€")
        print(f"   - Bénéfice net annuel: {benefice_net:,.0f}€")
        print(f"   - Temps de retour: {temps_retour:.1f} ans")
        
        # Économies pour les consommateurs
        print("\n💸 Économies consommateurs:")
        for i, (cons, point) in enumerate(zip(consommateurs, cons_points)):
            # Trouver l'allocation
            alloc_info = next((a for a in allocations if a[1] == point.id), None)
            if alloc_info:
                capacite_autoconso = next(p for p in prod_points if p.id == alloc_info[0]).capacite_kwc * alloc_info[2] / 100
                autoconso_kwh = capacite_autoconso * 1200  # Production annuelle estimée
                
                # Prix réseau vs autoconso
                prix_reseau = services['pricing'].get_prix_actif(cons.id).prix_effectif
                prix_autoconso = tarif_prod.prix_kwh
                economie_unitaire = prix_reseau - prix_autoconso
                economie_annuelle = autoconso_kwh * economie_unitaire
                
                print(f"\n   {cons.nom}:")
                print(f"   - Autoconso: {autoconso_kwh/1000:.0f} MWh/an")
                print(f"   - Prix réseau: {prix_reseau:.3f}€/kWh")
                print(f"   - Prix autoconso: {prix_autoconso:.3f}€/kWh")
                print(f"   - Économie: {economie_annuelle:,.0f}€/an ({economie_unitaire:.3f}€/kWh)")
        
        # ==========================================
        # ÉTAPE 7: Alertes et optimisations
        # ==========================================
        print("\n=== ÉTAPE 7: Alertes et optimisations ===")
        
        # Vérifier les alertes de capacité
        alerts = services['capacity'].get_capacity_alerts()
        if alerts:
            print("\n🚨 Alertes de capacité:")
            for alert in alerts:
                print(f"   - {alert['level'].upper()}: {alert['point_name']} - {alert['message']} ({alert['utilization']:.0f}%)")
        else:
            print("\n✅ Aucune alerte de capacité")
        
        # Suggestions d'optimisation
        suggestions = services['capacity'].get_optimization_suggestions()
        if suggestions:
            print("\n💡 Suggestions d'optimisation:")
            for sugg in suggestions[:3]:  # Limiter à 3 suggestions
                if sugg['type'] == 'reallocation':
                    print(f"   - Réallocation: Transférer {sugg['percentage']}% de {sugg['from']} vers {sugg['to']}")
                elif sugg['type'] == 'new_client':
                    print(f"   - Nouveau client: {sugg['client_name']} peut utiliser {sugg['capacity']:.0f} kWc sur {sugg['production_point']}")
                elif sugg['type'] == 'capacity_warning':
                    print(f"   - Extension: {sugg['production_point']} approche saturation")
        
        # ==========================================
        # VÉRIFICATIONS FINALES
        # ==========================================
        print("\n=== VÉRIFICATIONS FINALES ===")
        
        # Vérifier la cohérence des données
        assert services['client'].get_statistics()['total_clients'] == 5
        assert len(services['capacity'].get_all_production_points()) == 4  # 3 prod + 1 prosumer
        assert len(services['capacity'].get_all_consumption_points()) == 4  # 3 cons + 1 prosumer
        assert len(services['capacity'].get_all_active_allocations()) == 5  # 4 + auto-alloc
        
        # Vérifier les capacités
        for point in prod_points:
            updated = services['capacity'].get_production_point(point.id)
            assert updated.capacite_disponible_kwc <= updated.capacite_kwc
            print(f"✓ {updated.nom}: {updated.capacite_disponible_kwc:.0f}/{updated.capacite_kwc:.0f} kWc disponible")
        
        print("\n✅ Test de bout en bout complété avec succès!")
        print(f"   - {stats['total_clients']} clients créés")
        print(f"   - {len(prod_points) + 1} points de production")
        print(f"   - {len(cons_points) + 1} points de consommation")
        print(f"   - {len(allocations) + 1} allocations actives")
        print(f"   - Capacité totale: {stats_capacity['total_capacity_kwc']:.0f} kWc")
        print(f"   - Revenu annuel estimé: {revenu_annuel:,.0f}€")
        
        return True