"""
Main UI module for PMO billing system
Streamlit interface for managing billing operations
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import logging
import io

from .database import BillingDatabase
from .models import (
    Project, Participant, ParticipantType, ProjectStatus,
    Invoice, InvoiceStatus, BillingCalculation, BillingPeriod
)
from .invoice_generator import InvoiceGenerator
from .email_sender import EmailSender
from .integration_helper import OptimPVIntegration

logger = logging.getLogger(__name__)

def show_facturation_page():
    """Main billing page interface"""
    
    st.title("💰 Facturation PMO")
    st.markdown("Gestion de la facturation pour l'autoconsommation collective photovoltaïque")
    
    # Initialize database and services
    if 'billing_db' not in st.session_state:
        st.session_state.billing_db = BillingDatabase()
    
    if 'invoice_generator' not in st.session_state:
        st.session_state.invoice_generator = InvoiceGenerator(st.session_state.billing_db)
    
    if 'email_sender' not in st.session_state:
        st.session_state.email_sender = EmailSender(st.session_state.billing_db)
    
    db = st.session_state.billing_db
    invoice_gen = st.session_state.invoice_generator
    email_sender = st.session_state.email_sender
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choisir une section",
        [
            "📊 Tableau de Bord",
            "🏗️ Gestion des Projets",
            "👥 Gestion des Participants",
            "📈 Données de Production/Consommation",
            "🧾 Génération de Factures",
            "📧 Envoi et Suivi",
            "⚙️ Configuration"
        ]
    )
    
    # Route to appropriate page
    if "Tableau de Bord" in page:
        show_dashboard(db)
    elif "Gestion des Projets" in page:
        show_project_management(db)
    elif "Gestion des Participants" in page:
        show_participant_management(db)
    elif "Données de Production" in page:
        show_data_management(db)
    elif "Génération de Factures" in page:
        show_invoice_generation(db, invoice_gen)
    elif "Envoi et Suivi" in page:
        show_email_management(db, email_sender, invoice_gen)
    elif "Configuration" in page:
        show_configuration(db, email_sender)

def show_dashboard(db: BillingDatabase):
    """Dashboard with key metrics and overview"""
    
    st.header("📊 Tableau de Bord")
    
    # Get projects and calculate metrics
    projects = db.get_projects()
    
    if not projects:
        st.info("Aucun projet configuré. Commencez par créer un projet dans la section 'Gestion des Projets'.")
        
        # Proposer l'import automatique depuis la configuration
        if st.button("🔄 Importer le projet depuis la configuration OptimPV", type="primary"):
            with st.spinner("Import en cours..."):
                # Récupérer les données du projet
                project_data = OptimPVIntegration.get_project_from_config()
                
                if project_data and project_data.get('name'):
                    # Créer le projet
                    project_id = db.create_project(project_data)
                    
                    if project_id:
                        # Ajouter les participants depuis les clés de répartition
                        participants = OptimPVIntegration.get_participants_from_repartition_keys()
                        
                        for participant in participants:
                            participant['project_id'] = project_id
                            db.create_participant(participant)
                        
                        st.success(f"✅ Projet '{project_data['name']}' importé avec {len(participants)} participants!")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la création du projet")
                else:
                    st.warning("Aucune configuration de projet trouvée. Veuillez d'abord configurer votre projet dans OptimPV.")
        
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Projets Actifs", len([p for p in projects if p['status'] == 'active']))
    
    with col2:
        total_participants = sum(len(db.get_participants(p['id'])) for p in projects)
        st.metric("Participants", total_participants)
    
    with col3:
        # TODO: Calculate from actual billing data
        st.metric("CA Mensuel", "15,240 €", delta="2,340 €")
    
    with col4:
        # TODO: Calculate pending invoices
        st.metric("Factures en Attente", "7", delta="-2")
    
    st.markdown("---")
    
    # Projects overview
    st.subheader("🏗️ Aperçu des Projets")
    
    if projects:
        df_projects = pd.DataFrame(projects)
        
        # Select and rename columns for display
        display_cols = {
            'name': 'Nom',
            'client_name': 'Client',
            'status': 'Statut',
            'total_capacity_kwc': 'Puissance (kWc)',
            'created_at': 'Créé le'
        }
        
        df_display = df_projects[list(display_cols.keys())].rename(columns=display_cols)
        
        # Format dates
        if 'Créé le' in df_display.columns:
            df_display['Créé le'] = pd.to_datetime(df_display['Créé le']).dt.strftime('%d/%m/%Y')
        
        st.dataframe(df_display, use_container_width=True)
    
    # Recent activity
    st.subheader("📈 Activité Récente")
    st.info("Fonctionnalité de suivi d'activité à venir")

def show_project_management(db: BillingDatabase):
    """Project management interface"""
    
    st.header("🏗️ Gestion des Projets")
    
    tab1, tab2 = st.tabs(["📋 Liste des Projets", "➕ Nouveau Projet"])
    
    with tab1:
        projects = db.get_projects()
        
        if projects:
            st.subheader("Projets Existants")
            
            for project in projects:
                with st.expander(f"🏗️ {project['name']} - {project['client_name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Adresse:** {project['address'] or 'Non spécifiée'}")
                        st.write(f"**Email Client:** {project['client_email'] or 'Non spécifié'}")
                        st.write(f"**Téléphone:** {project['client_phone'] or 'Non spécifié'}")
                        st.write(f"**Statut:** {project['status']}")
                    
                    with col2:
                        st.write(f"**Puissance Totale:** {project['total_capacity_kwc']} kWc")
                        st.write(f"**Investissement:** {project['total_investment']:,.0f} € TTC")
                        st.write(f"**% Financement:** {project['financing_percentage']}%")
                        st.write(f"**Production Annuelle:** {project['annual_production_kwh']:,.0f} kWh")
                    
                    # Participants count
                    participants = db.get_participants(project['id'])
                    st.info(f"👥 {len(participants)} participant(s) configuré(s)")
        else:
            st.info("Aucun projet créé pour le moment.")
    
    with tab2:
        st.subheader("Créer un Nouveau Projet")
        
        with st.form("new_project_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nom du Projet*", placeholder="Ex: Installation Solaire Mougins")
                client_name = st.text_input("Nom du Client*", placeholder="Ex: Copropriété Les Jardins")
                address = st.text_area("Adresse", placeholder="Adresse complète du projet")
                client_email = st.text_input("Email Client", placeholder="contact@client.com")
                client_phone = st.text_input("Téléphone Client", placeholder="+33 X XX XX XX XX")
            
            with col2:
                start_date = st.date_input("Date de Début", value=date.today())
                end_date = st.date_input("Date de Fin", value=date.today() + timedelta(days=365*20))
                total_capacity_kwc = st.number_input("Puissance Totale (kWc)", min_value=0.0, value=100.0, step=1.0)
                total_investment = st.number_input("Investissement Total (€ TTC)", min_value=0.0, value=150000.0, step=1000.0)
                financing_percentage = st.slider("Pourcentage de Financement (%)", 0, 100, 80)
                annual_production_kwh = st.number_input("Production Annuelle Estimée (kWh)", min_value=0.0, value=120000.0, step=1000.0)
            
            submitted = st.form_submit_button("✅ Créer le Projet", type="primary")
            
            if submitted:
                if name and client_name:
                    project_data = {
                        'name': name,
                        'client_name': client_name,
                        'address': address,
                        'client_email': client_email,
                        'client_phone': client_phone,
                        'start_date': start_date,
                        'end_date': end_date,
                        'total_capacity_kwc': total_capacity_kwc,
                        'total_investment': total_investment,
                        'financing_percentage': financing_percentage,
                        'annual_production_kwh': annual_production_kwh
                    }
                    
                    project_id = db.create_project(project_data)
                    if project_id:
                        st.success(f"✅ Projet '{name}' créé avec succès ! ID: {project_id}")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la création du projet")
                else:
                    st.error("Veuillez remplir au minimum le nom du projet et le nom du client")

def show_participant_management(db: BillingDatabase):
    """Participant management interface"""
    
    st.header("👥 Gestion des Participants")
    
    # Project selection
    projects = db.get_projects()
    if not projects:
        st.warning("Aucun projet disponible. Créez d'abord un projet.")
        return
    
    project_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in projects}
    selected_project_name = st.selectbox("Sélectionner un Projet", list(project_options.keys()))
    selected_project_id = project_options[selected_project_name]
    
    tab1, tab2 = st.tabs(["📋 Participants Existants", "➕ Nouveau Participant"])
    
    with tab1:
        participants = db.get_participants(selected_project_id)
        
        if participants:
            st.subheader(f"Participants du Projet (Total: {len(participants)})")
            
            # Summary by type
            producers = [p for p in participants if p['type'] == 'producer']
            consumers = [p for p in participants if p['type'] == 'consumer']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🏭 Producteurs", len(producers))
            with col2:
                st.metric("🏠 Consommateurs", len(consumers))
            
            # Participants table
            df_participants = pd.DataFrame(participants)
            display_cols = {
                'name': 'Nom',
                'type': 'Type',
                'address': 'Adresse',
                'contact_email': 'Email',
                'allocation_percentage': 'Allocation (%)',
                'annual_consumption_kwh': 'Consommation Annuelle (kWh)'
            }
            
            df_display = df_participants[list(display_cols.keys())].rename(columns=display_cols)
            
            # Format type
            df_display['Type'] = df_display['Type'].map({
                'producer': '🏭 Producteur',
                'consumer': '🏠 Consommateur'
            })
            
            st.dataframe(df_display, use_container_width=True)
            
            # Allocation validation
            total_allocation = sum(p['allocation_percentage'] or 0 for p in participants)
            if abs(total_allocation - 100.0) < 0.01:
                st.success(f"✅ Allocation totale: {total_allocation:.1f}% (Valide)")
            else:
                st.error(f"❌ Allocation totale: {total_allocation:.1f}% (Doit être 100%)")
        else:
            st.info("Aucun participant configuré pour ce projet.")
    
    with tab2:
        st.subheader("Ajouter un Nouveau Participant")
        
        with st.form("new_participant_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Nom du Participant*", placeholder="Ex: Appartement A01")
                participant_type = st.selectbox("Type*", ["consumer", "producer"], 
                                              format_func=lambda x: "🏠 Consommateur" if x == "consumer" else "🏭 Producteur")
                address = st.text_area("Adresse", placeholder="Adresse du participant")
                contact_email = st.text_input("Email de Contact", placeholder="contact@participant.com")
                contact_phone = st.text_input("Téléphone", placeholder="+33 X XX XX XX XX")
            
            with col2:
                consumption_profile_id = st.text_input("ID Profil de Consommation", 
                                                     placeholder="Ex: RES_001", 
                                                     help="Identifiant du profil de consommation Enedis")
                allocation_percentage = st.number_input("Pourcentage d'Allocation (%)*", 
                                                       min_value=0.0, max_value=100.0, 
                                                       value=10.0, step=0.1)
                annual_consumption_kwh = st.number_input("Consommation Annuelle (kWh)", 
                                                        min_value=0.0, value=3000.0, step=100.0)
            
            submitted = st.form_submit_button("✅ Ajouter le Participant", type="primary")
            
            if submitted:
                if name and participant_type:
                    participant_data = {
                        'project_id': selected_project_id,
                        'name': name,
                        'type': participant_type,
                        'address': address,
                        'contact_email': contact_email,
                        'contact_phone': contact_phone,
                        'consumption_profile_id': consumption_profile_id,
                        'allocation_percentage': allocation_percentage,
                        'annual_consumption_kwh': annual_consumption_kwh
                    }
                    
                    participant_id = db.create_participant(participant_data)
                    if participant_id:
                        st.success(f"✅ Participant '{name}' ajouté avec succès ! ID: {participant_id}")
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'ajout du participant")
                else:
                    st.error("Veuillez remplir au minimum le nom et le type du participant")

def show_data_management(db: BillingDatabase):
    """Data management for production and consumption"""
    
    st.header("📈 Données de Production/Consommation")
    
    # Project selection
    projects = db.get_projects()
    if not projects:
        st.warning("Aucun projet disponible.")
        return
    
    project_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in projects}
    selected_project_name = st.selectbox("Sélectionner un Projet", list(project_options.keys()))
    selected_project_id = project_options[selected_project_name]
    
    # Bouton d'import automatique
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("🔄 Synchronisation avec les données OptimPV disponible")
    with col2:
        if st.button("🔄 Importer depuis OptimPV", type="primary"):
            with st.spinner("Import des données en cours..."):
                # Récupérer les données depuis les modules OptimPV
                data = OptimPVIntegration.get_production_consumption_data()
                
                if not data['production'].empty:
                    # Enregistrer les données de production
                    for _, row in data['production'].iterrows():
                        production_data = {
                            'total_production_kwh': row.get('production_kwh', 0),
                            'autoconsumption_kwh': row.get('autoconsommation_kwh', 0),
                            'injection_kwh': row.get('injection_kwh', 0)
                        }
                        
                        row_date = pd.to_datetime(row['date'])
                        db.record_monthly_production(
                            selected_project_id,
                            row_date.year,
                            row_date.month,
                            production_data
                        )
                    
                    st.success(f"✅ {len(data['production'])} mois de données de production importés")
                
                if not data['consumption'].empty:
                    # Enregistrer les données de consommation par participant
                    participants = db.get_participants(selected_project_id)
                    participant_map = {p['name']: p['id'] for p in participants}
                    
                    imported_count = 0
                    for _, row in data['consumption'].iterrows():
                        participant_name = row.get('participant')
                        if participant_name in participant_map:
                            consumption_data = {
                                'consumption_kwh': row.get('consumption_kwh', 0),
                                'autoconsumption_kwh': row.get('autoconsommation_kwh', 0),
                                'grid_consumption_kwh': row.get('grid_consumption_kwh', 0)
                            }
                            
                            row_date = pd.to_datetime(row['date'])
                            db.record_monthly_consumption(
                                participant_map[participant_name],
                                row_date.year,
                                row_date.month,
                                consumption_data
                            )
                            imported_count += 1
                    
                    st.success(f"✅ {imported_count} enregistrements de consommation importés")
                
                st.rerun()
    
    tab1, tab2, tab3 = st.tabs(["📊 Données de Production", "🏠 Données de Consommation", "📥 Import Manuel"])
    
    with tab1:
        st.subheader("Données de Production Mensuelle")
        
        # Afficher les données existantes
        with st.spinner("Chargement des données..."):
            # TODO: Créer une méthode dans database.py pour récupérer les données de production
            st.info("Visualisation des données de production à implémenter")
    
    with tab2:
        st.subheader("Données de Consommation des Participants")
        
        # Afficher les données existantes
        with st.spinner("Chargement des données..."):
            # TODO: Créer une méthode dans database.py pour récupérer les données de consommation
            st.info("Visualisation des données de consommation à implémenter")
    
    with tab3:
        st.subheader("Import Manuel de Données")
        st.info("💡 Utilisez le bouton 'Importer depuis OptimPV' ci-dessus pour synchroniser automatiquement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Import Production Mensuelle")
            with st.form("manual_production"):
                year = st.number_input("Année", value=datetime.now().year, min_value=2020, max_value=2030)
                month = st.number_input("Mois", value=datetime.now().month, min_value=1, max_value=12)
                total_production = st.number_input("Production Totale (kWh)", min_value=0.0, value=8000.0)
                autoconsumption = st.number_input("Autoconsommation (kWh)", min_value=0.0, value=6000.0)
                injection = st.number_input("Injection Réseau (kWh)", min_value=0.0, value=2000.0)
                
                if st.form_submit_button("Enregistrer Production"):
                    production_data = {
                        'total_production_kwh': total_production,
                        'autoconsumption_kwh': autoconsumption,
                        'injection_kwh': injection
                    }
                    
                    if db.record_monthly_production(selected_project_id, year, month, production_data):
                        st.success("✅ Données de production enregistrées")
                    else:
                        st.error("Erreur lors de l'enregistrement")
        
        with col2:
            st.markdown("##### Import Consommation Participant")
            participants = db.get_participants(selected_project_id)
            
            if participants:
                with st.form("manual_consumption"):
                    participant_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in participants}
                    selected_participant_name = st.selectbox("Participant", list(participant_options.keys()))
                    selected_participant_id = participant_options[selected_participant_name]
                    
                    year = st.number_input("Année", value=datetime.now().year, min_value=2020, max_value=2030, key="cons_year")
                    month = st.number_input("Mois", value=datetime.now().month, min_value=1, max_value=12, key="cons_month")
                    total_consumption = st.number_input("Consommation Totale (kWh)", min_value=0.0, value=300.0)
                    participant_autoconsumption = st.number_input("Autoconsommation (kWh)", min_value=0.0, value=200.0)
                    grid_consumption = st.number_input("Consommation Réseau (kWh)", min_value=0.0, value=100.0)
                    
                    if st.form_submit_button("Enregistrer Consommation"):
                        consumption_data = {
                            'consumption_kwh': total_consumption,
                            'autoconsumption_kwh': participant_autoconsumption,
                            'grid_consumption_kwh': grid_consumption
                        }
                        
                        if db.record_monthly_consumption(selected_participant_id, year, month, consumption_data):
                            st.success("✅ Données de consommation enregistrées")
                        else:
                            st.error("Erreur lors de l'enregistrement")
            else:
                st.warning("Aucun participant configuré pour ce projet")

def show_invoice_generation(db: BillingDatabase, invoice_gen: InvoiceGenerator):
    """Invoice generation interface"""
    
    st.header("🧾 Génération de Factures")
    
    # Project selection
    projects = db.get_projects()
    if not projects:
        st.warning("Aucun projet disponible.")
        return
    
    project_options = {f"{p['name']} (ID: {p['id']})": p['id'] for p in projects}
    selected_project_name = st.selectbox("Sélectionner un Projet", list(project_options.keys()))
    selected_project_id = project_options[selected_project_name]
    selected_project = next(p for p in projects if p['id'] == selected_project_id)
    
    tab1, tab2 = st.tabs(["🆕 Nouvelle Période de Facturation", "📋 Factures Existantes"])
    
    with tab1:
        st.subheader("Créer une Nouvelle Période de Facturation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            period_name = st.text_input("Nom de la Période", value=f"Période {datetime.now().strftime('%m/%Y')}")
            start_date = st.date_input("Date de Début", value=date.today().replace(day=1))
            end_date = st.date_input("Date de Fin", value=date.today())
        
        with col2:
            # Récupérer le prix optimal depuis l'analyse
            optimal_price = OptimPVIntegration.get_optimal_price()
            
            autoconsumption_price = st.number_input(
                "Prix de l'Autoconsommation (€/kWh)", 
                value=optimal_price,
                step=0.001,
                format="%.4f",
                help=f"Prix optimal calculé par OptimPV: {optimal_price:.4f} €/kWh"
            )
            tax_rate = st.number_input(
                "Taux de TVA (%)",
                value=float(db.get_setting('tax_rate') or 0.20) * 100,
                step=0.1
            ) / 100
            payment_terms_days = st.number_input("Délai de Paiement (jours)", value=30, min_value=1)
        
        if st.button("🧮 Calculer les Factures", type="primary"):
            participants = db.get_participants(selected_project_id)
            
            if not participants:
                st.error("Aucun participant configuré pour ce projet")
                return
            
            # Récupérer les données réelles depuis OptimPV
            data = OptimPVIntegration.get_production_consumption_data()
            
            # Calculer pour chaque participant
            calculations = []
            
            # Utiliser les données d'intégration si disponibles
            if not data['production'].empty and not data['consumption'].empty:
                billing_data = OptimPVIntegration.calculate_monthly_billing_from_data(
                    data['production'], 
                    data['consumption'],
                    [p for p in participants if p['type'] == 'consumer'],
                    end_date.year,
                    end_date.month
                )
                
                for billing_item in billing_data:
                    # Trouver le participant correspondant
                    participant = next((p for p in participants if p['name'] == billing_item['participant_name']), None)
                    
                    if participant:
                        calc = BillingCalculation(
                            participant_id=participant['id'],
                            participant_name=participant['name'],
                            period_start=start_date,
                            period_end=end_date,
                            autoconsumption_kwh=billing_item['autoconsumption_kwh'],
                            unit_price_eur_kwh=autoconsumption_price
                        )
                        calc.calculate(tax_rate)
                        calculations.append(calc)
            else:
                # Utiliser les allocations pour répartir une production estimée
                st.warning("Données de production/consommation non disponibles. Utilisation d'estimations basées sur les allocations.")
                
                # Estimation mensuelle basée sur la production annuelle
                annual_production = selected_project.get('annual_production_kwh', 120000)
                monthly_production = annual_production / 12
                monthly_autoconso = monthly_production * 0.75  # 75% d'autoconsommation
                
                for participant in participants:
                    if participant['type'] == 'consumer':
                        participant_autoconso = monthly_autoconso * (participant['allocation_percentage'] / 100)
                        
                        calc = BillingCalculation(
                            participant_id=participant['id'],
                            participant_name=participant['name'],
                            period_start=start_date,
                            period_end=end_date,
                            autoconsumption_kwh=participant_autoconso,
                            unit_price_eur_kwh=autoconsumption_price
                        )
                        calc.calculate(tax_rate)
                        calculations.append(calc)
            
            # Display calculations
            st.subheader("📊 Aperçu des Factures")
            
            calc_data = []
            for calc in calculations:
                calc_data.append({
                    'Participant': calc.participant_name,
                    'Autoconsommation (kWh)': f"{calc.autoconsumption_kwh:.2f}",
                    'Prix Unitaire (€/kWh)': f"{calc.unit_price_eur_kwh:.4f}",
                    'Sous-total HT (€)': f"{calc.subtotal:.2f}",
                    'TVA (€)': f"{calc.tax_amount:.2f}",
                    'Total TTC (€)': f"{calc.total_amount:.2f}"
                })
            
            df_calc = pd.DataFrame(calc_data)
            st.dataframe(df_calc, use_container_width=True)
            
            # Totals
            total_kwh = sum(calc.autoconsumption_kwh for calc in calculations)
            total_amount = sum(calc.total_amount for calc in calculations)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Autoconsommation", f"{total_kwh:.2f} kWh")
            with col2:
                st.metric("Montant Total HT", f"{sum(calc.subtotal for calc in calculations):.2f} €")
            with col3:
                st.metric("Montant Total TTC", f"{total_amount:.2f} €")
            
            # Generate button
            if st.button("✅ Générer les Factures", type="primary"):
                with st.spinner("Génération des factures en cours..."):
                    # Create billing period
                    billing_data = {
                        'project_id': selected_project_id,
                        'period_name': period_name,
                        'start_date': start_date,
                        'end_date': end_date,
                        'total_amount': total_amount,
                        'payment_due_date': end_date + timedelta(days=payment_terms_days)
                    }
                    
                    billing_period_id = db.create_billing_period(billing_data)
                    
                    if billing_period_id:
                        st.success(f"✅ Période de facturation créée (ID: {billing_period_id})")
                        st.success(f"✅ {len(calculations)} factures générées avec succès")
                        
                        # Generate summary PDF
                        try:
                            project_obj = Project.from_dict(selected_project)
                            summary_pdf = invoice_gen.generate_billing_summary_pdf(
                                project_obj, calculations, period_name
                            )
                            
                            if summary_pdf:
                                st.download_button(
                                    "📥 Télécharger le Résumé PDF",
                                    summary_pdf,
                                    file_name=f"resume_facturation_{period_name.replace(' ', '_')}.pdf",
                                    mime="application/pdf"
                                )
                        except Exception as e:
                            st.warning(f"Erreur lors de la génération du PDF: {e}")
                    else:
                        st.error("Erreur lors de la création de la période de facturation")
    
    with tab2:
        st.subheader("Factures Existantes")
        st.info("🚧 Liste et gestion des factures existantes à implémenter")

def show_email_management(db: BillingDatabase, email_sender: EmailSender, invoice_gen: InvoiceGenerator):
    """Email management and sending interface"""
    
    st.header("📧 Envoi et Suivi des Factures")
    
    if not email_sender.smtp_configured:
        st.warning("⚠️ Configuration SMTP requise pour l'envoi d'emails. Configurez-la dans la section Configuration.")
    
    tab1, tab2 = st.tabs(["📤 Envoi d'Emails", "📊 Suivi des Paiements"])
    
    with tab1:
        st.subheader("Envoi de Factures par Email")
        st.info("🚧 Interface d'envoi d'emails à implémenter")
        
        if email_sender.smtp_configured:
            st.success("✅ SMTP configuré - Prêt pour l'envoi")
        else:
            st.error("❌ SMTP non configuré")
    
    with tab2:
        st.subheader("Suivi des Paiements")
        st.info("🚧 Interface de suivi des paiements à implémenter")

def show_configuration(db: BillingDatabase, email_sender: EmailSender):
    """Configuration interface"""
    
    st.header("⚙️ Configuration")
    
    tab1, tab2, tab3 = st.tabs(["🏢 Société", "📧 Email SMTP", "💰 Facturation"])
    
    with tab1:
        st.subheader("Informations de la Société")
        
        with st.form("company_config"):
            company_name = st.text_input("Nom de la Société", value=db.get_setting('company_name') or '')
            company_address = st.text_area("Adresse", value=db.get_setting('company_address') or '')
            company_siret = st.text_input("Numéro SIRET", value=db.get_setting('company_siret') or '')
            
            if st.form_submit_button("💾 Sauvegarder"):
                db.set_setting('company_name', company_name)
                db.set_setting('company_address', company_address)
                db.set_setting('company_siret', company_siret)
                st.success("✅ Informations de société sauvegardées")
    
    with tab2:
        st.subheader("Configuration SMTP pour l'Envoi d'Emails")
        
        with st.form("smtp_config"):
            smtp_server = st.text_input("Serveur SMTP", value=db.get_setting('smtp_server') or '')
            smtp_port = st.number_input("Port", value=int(db.get_setting('smtp_port') or 587), min_value=1, max_value=65535)
            smtp_username = st.text_input("Nom d'utilisateur", value=db.get_setting('smtp_username') or '')
            smtp_password = st.text_input("Mot de passe", type="password")
            smtp_use_tls = st.checkbox("Utiliser TLS", value=db.get_setting('smtp_use_tls') == 'True')
            
            if st.form_submit_button("🔧 Configurer et Tester"):
                if smtp_server and smtp_username and smtp_password:
                    if email_sender.configure_smtp(smtp_server, smtp_port, smtp_username, smtp_password, smtp_use_tls):
                        st.success("✅ Configuration SMTP réussie et testée")
                    else:
                        st.error("❌ Échec de la configuration SMTP")
                else:
                    st.error("Veuillez remplir tous les champs obligatoires")
    
    with tab3:
        st.subheader("Paramètres de Facturation")
        
        # Intégration avec les paramètres OptimPV
        company_info = OptimPVIntegration.get_company_info_from_config()
        
        with st.form("billing_config"):
            # Prix optimal depuis l'analyse
            optimal_price = OptimPVIntegration.get_optimal_price()
            
            autoconsumption_price = st.number_input(
                "Prix de l'Autoconsommation (€/kWh)",
                value=optimal_price,
                step=0.001,
                format="%.4f",
                help=f"Prix optimal calculé: {optimal_price:.4f} €/kWh"
            )
            tax_rate = st.number_input(
                "Taux de TVA (%)",
                value=float(db.get_setting('tax_rate') or 0.20) * 100,
                step=0.1
            )
            invoice_prefix = st.text_input("Préfixe des Factures", value=db.get_setting('invoice_prefix') or 'PMO')
            payment_terms_days = st.number_input(
                "Délai de Paiement par Défaut (jours)",
                value=int(db.get_setting('default_payment_terms_days') or 30),
                min_value=1
            )
            
            if st.form_submit_button("💾 Sauvegarder"):
                db.set_setting('autoconsumption_price_eur_kwh', str(autoconsumption_price))
                db.set_setting('tax_rate', str(tax_rate / 100))
                db.set_setting('invoice_prefix', invoice_prefix)
                db.set_setting('default_payment_terms_days', str(payment_terms_days))
                st.success("✅ Paramètres de facturation sauvegardés")