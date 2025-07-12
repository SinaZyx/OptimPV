"""Connecteur pour l'intégration avec le module d'analyse (core_analyzer).

Ce module permet la sélection et l'utilisation des données clients
dans les analyses financières et optimisations d'OptimPV.
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any
from datetime import date

from ..models.client import Client
from ..services.client_service import ClientService
from ..services.pricing_service import PricingService

logger = logging.getLogger(__name__)


class AnalysisConnector:
    """Connecteur pour l'intégration avec le core analyzer."""
    
    def __init__(self, client_service: ClientService = None, pricing_service: PricingService = None):
        """Initialise le connecteur d'analyse.
        
        Args:
            client_service: Service ERP clients
            pricing_service: Service ERP prix
        """
        self.client_service = client_service or ClientService()
        self.pricing_service = pricing_service or PricingService()
        
    def set_client_context(self, client_id: int) -> bool:
        """Définit le contexte client pour les analyses.
        
        Cette méthode configure le client sélectionné et ses tarifs
        pour utilisation dans le module d'analyse financière.
        
        Args:
            client_id: ID du client à sélectionner
            
        Returns:
            True si contexte défini avec succès
        """
        try:
            # Récupérer le client
            client = self.client_service.get_by_id(client_id)
            if not client:
                logger.error(f"Client {client_id} introuvable")
                return False
                
            # Récupérer le prix actif
            prix = self.pricing_service.get_active_price(client_id)
            if not prix:
                logger.warning(f"Aucun prix actif pour le client {client.nom}")
                st.warning(f"⚠️ Le client '{client.nom}' n'a pas de prix défini")
                return False
                
            # Stocker dans la session Streamlit
            st.session_state.current_client = client
            st.session_state.client_pricing = {
                'prix_kwh': prix.prix_kwh,
                'type_tarif': prix.type_tarif,
                'reference_prix': prix.reference_prix,
                'remise_pourcentage': prix.remise_pourcentage,
                'client_id': client.id,
                'client_name': client.nom,
                'client_code': client.code_client,
                'client_type': client.type_client
            }
            
            # Ajouter des informations supplémentaires utiles
            if client.zone_geographique:
                st.session_state.client_pricing['zone'] = client.zone_geographique
                
            # Si le client a des allocations d'autoconso
            from ..services.capacity_service import CapacityService
            capacity_service = CapacityService()
            allocations = capacity_service.get_client_allocations(client_id)
            
            if allocations:
                total_kwc = sum(a['production']['puissance_allouee_kwc'] for a in allocations if a['statut'] == 'actif')
                st.session_state.client_pricing['autoconso_kwc'] = total_kwc
                
            logger.info(f"Contexte client défini: {client.nom} - {prix.prix_kwh} €/kWh")
            return True
            
        except Exception as e:
            logger.error(f"Erreur définition contexte client: {e}")
            return False
            
    def get_client_pricing_for_analysis(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les données tarifaires d'un client pour l'analyse.
        
        Args:
            client_id: ID du client
            
        Returns:
            Dictionnaire avec les données tarifaires ou None
        """
        try:
            client = self.client_service.get_by_id(client_id)
            if not client:
                return None
                
            prix = self.pricing_service.get_active_price(client_id)
            if not prix:
                return None
                
            # Projections de prix
            projections = self.pricing_service.project_prices(
                client_id=client_id,
                years=25,  # Horizon standard pour PV
                inflation_rate=2.5  # Taux par défaut
            )
            
            return {
                'client': {
                    'id': client.id,
                    'code': client.code_client,
                    'nom': client.nom,
                    'type': client.type_client,
                    'zone': client.zone_geographique
                },
                'prix_actuel': {
                    'prix_kwh': prix.prix_kwh,
                    'type_tarif': prix.type_tarif,
                    'remise': prix.remise_pourcentage,
                    'date_debut': prix.date_debut.isoformat()
                },
                'projections': projections,
                'parametres': {
                    'inflation_energie': 2.5,
                    'inflation_generale': 2.0,
                    'augmentation_reseau': 3.0
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération pricing: {e}")
            return None
            
    def render_client_selector_widget(self) -> Optional[Client]:
        """Affiche un widget de sélection de client pour les analyses.
        
        Returns:
            Client sélectionné ou None
        """
        st.markdown("### 🏢 Sélection du client")
        
        clients = self.client_service.get_all(include_inactive=False)
        
        if not clients:
            st.warning("Aucun client actif dans la base de données")
            if st.button("➕ Créer un client"):
                st.session_state['show_erp_module'] = True
                st.session_state['erp_tab'] = 'new_client'
            return None
            
        # Grouper par type
        grouped = {
            'Consommateurs': [c for c in clients if c.type_client == 'consommateur'],
            'Producteurs': [c for c in clients if c.type_client == 'producteur'],
            'Prosumers': [c for c in clients if c.type_client == 'prosumer']
        }
        
        # Widget de sélection avec recherche
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Préparer les options
            options = []
            for group_name, group_clients in grouped.items():
                if group_clients:
                    options.append(f"--- {group_name} ---")
                    for client in group_clients:
                        prix = self.pricing_service.get_active_price(client.id)
                        prix_str = f" - {prix.prix_kwh:.4f} €/kWh" if prix else " - Sans prix"
                        options.append(f"{client.nom} ({client.code_client}){prix_str}")
                        
            selected = st.selectbox(
                "Client pour l'analyse",
                options=options,
                index=0 if st.session_state.get('current_client') is None else None
            )
            
        with col2:
            if st.button("🔄 Actualiser", use_container_width=True):
                st.rerun()
                
        # Traiter la sélection
        if selected and not selected.startswith("---"):
            # Extraire le code client
            code_client = selected.split("(")[1].split(")")[0]
            client = self.client_service.get_by_code(code_client)
            
            if client:
                # Afficher les infos du client
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Type", client.type_client.value.capitalize())
                    
                with col2:
                    prix = self.pricing_service.get_active_price(client.id)
                    if prix:
                        st.metric("Prix actuel", f"{prix.prix_kwh:.4f} €/kWh")
                    else:
                        st.metric("Prix", "Non défini")
                        
                with col3:
                    st.metric("Zone", client.zone_geographique or "N/A")
                    
                with col4:
                    if st.button("✅ Sélectionner", type="primary"):
                        if self.set_client_context(client.id):
                            st.success(f"✅ Client '{client.nom}' sélectionné")
                            return client
                        else:
                            st.error("❌ Impossible de sélectionner ce client")
                            
        return None
        
    def get_comparative_analysis_data(self, client_id: int) -> Dict[str, Any]:
        """Récupère les données pour une analyse comparative.
        
        Args:
            client_id: ID du client
            
        Returns:
            Données comparatives pour l'analyse
        """
        try:
            # Prix du client
            client_pricing = self.get_client_pricing_for_analysis(client_id)
            if not client_pricing:
                return {}
                
            # Prix moyens par zone
            client = self.client_service.get_by_id(client_id)
            zone_clients = []
            
            if client.zone_geographique:
                zone_clients = self.client_service.get_clients_by_zone(client.zone_geographique)
                
            # Calculer les statistiques de zone
            zone_prices = []
            for zc in zone_clients:
                prix = self.pricing_service.get_active_price(zc.id)
                if prix:
                    zone_prices.append(prix.prix_kwh)
                    
            zone_stats = {
                'count': len(zone_prices),
                'average': sum(zone_prices) / len(zone_prices) if zone_prices else 0,
                'min': min(zone_prices) if zone_prices else 0,
                'max': max(zone_prices) if zone_prices else 0
            }
            
            # Comparaison avec références
            comparisons = {}
            current_price = client_pricing['prix_actuel']['prix_kwh']
            
            for ref_name, ref_price in self.pricing_service.PRIX_REFERENCES.items():
                comparisons[ref_name] = {
                    'price': ref_price,
                    'difference': current_price - ref_price,
                    'percentage': ((current_price - ref_price) / ref_price) * 100
                }
                
            return {
                'client': client_pricing,
                'zone_statistics': zone_stats,
                'reference_comparisons': comparisons,
                'recommendation': self._generate_pricing_recommendation(
                    current_price,
                    zone_stats,
                    comparisons
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse comparative: {e}")
            return {}
            
    def _generate_pricing_recommendation(
        self,
        current_price: float,
        zone_stats: Dict[str, Any],
        comparisons: Dict[str, Any]
    ) -> str:
        """Génère une recommandation tarifaire.
        
        Args:
            current_price: Prix actuel du client
            zone_stats: Statistiques de la zone
            comparisons: Comparaisons avec références
            
        Returns:
            Texte de recommandation
        """
        recommendations = []
        
        # Comparaison avec la zone
        if zone_stats['count'] > 0:
            if current_price > zone_stats['average'] * 1.1:
                recommendations.append(
                    f"⚠️ Prix supérieur de {((current_price/zone_stats['average']-1)*100):.1f}% "
                    f"à la moyenne de la zone"
                )
            elif current_price < zone_stats['average'] * 0.9:
                recommendations.append(
                    f"✅ Prix avantageux: {((1-current_price/zone_stats['average'])*100):.1f}% "
                    f"sous la moyenne de la zone"
                )
                
        # Comparaison avec TRV
        trv_comparison = comparisons.get('EDF_TRV_BASE', {})
        if trv_comparison and trv_comparison['percentage'] < -10:
            recommendations.append(
                f"✅ Excellente compétitivité vs TRV: {abs(trv_comparison['percentage']):.1f}% "
                f"d'économie"
            )
        elif trv_comparison and trv_comparison['percentage'] > 0:
            recommendations.append(
                f"⚠️ Prix supérieur au TRV de {trv_comparison['percentage']:.1f}%"
            )
            
        return " | ".join(recommendations) if recommendations else "Prix dans la moyenne du marché"
        
    def export_client_data_for_report(self, client_id: int) -> Dict[str, Any]:
        """Exporte les données client pour inclusion dans les rapports.
        
        Args:
            client_id: ID du client
            
        Returns:
            Données formatées pour les rapports
        """
        try:
            client = self.client_service.get_by_id(client_id)
            if not client:
                return {}
                
            prix = self.pricing_service.get_active_price(client_id)
            
            # Données de base
            data = {
                'informations_client': {
                    'nom': client.nom,
                    'code': client.code_client,
                    'type': client.type_client.value.capitalize(),
                    'adresse': client.adresse_complete,
                    'contact': client.contact_principal or 'Non renseigné',
                    'telephone': client.telephone or 'Non renseigné',
                    'email': client.email or 'Non renseigné',
                    'siret': client.siret or 'Non renseigné'
                },
                'tarification': {
                    'prix_actuel': f"{prix.prix_kwh:.4f} €/kWh" if prix else 'Non défini',
                    'type_tarif': prix.type_tarif.value.capitalize() if prix else 'N/A',
                    'date_application': prix.date_debut.strftime('%d/%m/%Y') if prix else 'N/A'
                }
            }
            
            # Ajouter l'historique tarifaire
            history = self.pricing_service.get_price_history(client_id)
            if history:
                data['historique_tarifs'] = [
                    {
                        'periode': f"{p.date_debut.strftime('%d/%m/%Y')} - "
                                  f"{p.date_fin.strftime('%d/%m/%Y') if p.date_fin else 'En cours'}",
                        'prix': f"{p.prix_kwh:.4f} €/kWh",
                        'type': p.type_tarif.value.capitalize()
                    }
                    for p in history[:5]  # Limiter à 5 derniers
                ]
                
            return data
            
        except Exception as e:
            logger.error(f"Erreur export données client: {e}")
            return {}