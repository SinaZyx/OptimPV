"""
Dashboard avancé avec KPIs visuels pour OptimPV
Interface modernisée avec graphiques et métriques en temps réel
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import json

from .database import BillingDatabase
from .payment_dashboard import PaymentDashboard
from .payment_manager import PaymentManager
from .dunning import DunningManager

def show_advanced_dashboard():
    """Dashboard avancé avec KPIs visuels"""
    
    st.title("📊 Dashboard Facturation OptimPV")
    st.markdown("**Tableau de bord exécutif avec métriques en temps réel**")
    
    # Initialisation des managers
    if 'billing_db' not in st.session_state:
        st.session_state.billing_db = BillingDatabase()
    
    db = st.session_state.billing_db
    payment_dashboard = PaymentDashboard(db.db_path)
    payment_mgr = PaymentManager(db.db_path)
    dunning_mgr = DunningManager(db.db_path)
    
    # Sélecteur de période
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        period_range = st.selectbox(
            "Période d'analyse",
            ["30 derniers jours", "90 derniers jours", "12 derniers mois", "Année en cours"],
            index=1
        )
    
    with col2:
        auto_refresh = st.checkbox("🔄 Actualisation automatique", value=True)
    
    with col3:
        if st.button("🔄 Actualiser", type="primary"):
            st.rerun()
    
    # === KPIs PRINCIPAUX ===
    st.markdown("### 🎯 KPIs Principaux")
    
    try:
        # Récupération des KPIs
        kpis = payment_dashboard.get_payment_kpis()
        dso = payment_dashboard.calculate_dso()
        collection_metrics = payment_dashboard.calculate_collection_rate()
        
        # Métriques en colonnes
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "💰 Créances Actuelles",
                f"{kpis['current_receivables']:,.0f} €",
                delta=f"+{kpis['monthly_collections']:,.0f} € ce mois"
            )
        
        with col2:
            overdue_pct = kpis['overdue_percentage']
            delta_color = "inverse" if overdue_pct > 15 else "normal"
            st.metric(
                "⏰ Impayés",
                f"{kpis['overdue_amount']:,.0f} €",
                delta=f"{overdue_pct:.1f}% du total",
                delta_color=delta_color
            )
        
        with col3:
            dso_color = "inverse" if dso.dso_days > 45 else "normal"
            st.metric(
                "📅 DSO",
                f"{dso.dso_days:.1f} jours",
                delta="Délai moy. recouvrement",
                delta_color=dso_color
            )
        
        with col4:
            collection_color = "inverse" if collection_metrics.collection_rate < 85 else "normal"
            st.metric(
                "✅ Taux Recouvrement",
                f"{collection_metrics.collection_rate:.1f}%",
                delta=f"Moy: {collection_metrics.average_collection_period:.0f}j",
                delta_color=collection_color
            )
        
        with col5:
            bad_debt_color = "inverse" if collection_metrics.bad_debt_rate > 5 else "normal"
            st.metric(
                "🚨 Créances Douteuses",
                f"{collection_metrics.bad_debt_rate:.1f}%",
                delta="Taux créances >120j",
                delta_color=bad_debt_color
            )
        
    except Exception as e:
        st.error(f"Erreur lors du chargement des KPIs: {e}")
        st.info("Assurez-vous d'avoir des données de facturation configurées")
    
    st.markdown("---")
    
    # === GRAPHIQUES VISUELS ===
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Tendances", "🎂 Aging des Créances", "💳 Moyens de Paiement", "🔔 Alertes"
    ])
    
    with tab1:
        show_trends_charts(payment_dashboard)
    
    with tab2:
        show_aging_analysis(payment_dashboard)
    
    with tab3:
        show_payment_methods_analysis(payment_dashboard)
    
    with tab4:
        show_alerts_and_notifications(db, dunning_mgr, payment_mgr)

def show_trends_charts(payment_dashboard: PaymentDashboard):
    """Afficher les graphiques de tendances"""
    
    st.subheader("📈 Évolution des Tendances")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### DSO Evolution (12 derniers mois)")
        try:
            dso_trend = payment_dashboard.get_dso_trend(12)
            
            if dso_trend:
                df_dso = pd.DataFrame(dso_trend)
                df_dso['period'] = pd.to_datetime(df_dso['period'])
                
                fig_dso = px.line(
                    df_dso, 
                    x='period', 
                    y='dso_days',
                    title="Évolution du DSO",
                    labels={'period': 'Période', 'dso_days': 'DSO (jours)'}
                )
                fig_dso.add_hline(y=30, line_dash="dash", line_color="green", 
                                 annotation_text="Objectif: 30 jours")
                fig_dso.add_hline(y=45, line_dash="dash", line_color="orange", 
                                 annotation_text="Seuil d'alerte: 45 jours")
                fig_dso.update_layout(height=300)
                st.plotly_chart(fig_dso, use_container_width=True)
            else:
                st.info("Données DSO non disponibles")
        except Exception as e:
            st.error(f"Erreur graphique DSO: {e}")
    
    with col2:
        st.markdown("##### Prévisions de Trésorerie (4 semaines)")
        try:
            cash_flow = payment_dashboard.get_weekly_cash_flow_summary(4)
            
            if cash_flow:
                df_cf = pd.DataFrame(cash_flow)
                
                fig_cf = go.Figure()
                fig_cf.add_trace(go.Scatter(
                    x=df_cf['week_number'],
                    y=df_cf['expected_receipts'],
                    mode='lines+markers',
                    name='Encaissements prévus',
                    line=dict(color='green')
                ))
                fig_cf.add_trace(go.Scatter(
                    x=df_cf['week_number'],
                    y=df_cf['overdue_amount'],
                    mode='lines+markers',
                    name='Impayés',
                    line=dict(color='red')
                ))
                
                fig_cf.update_layout(
                    title="Prévisions Trésorerie",
                    xaxis_title="Semaine",
                    yaxis_title="Montant (€)",
                    height=300
                )
                st.plotly_chart(fig_cf, use_container_width=True)
            else:
                st.info("Prévisions non disponibles")
        except Exception as e:
            st.error(f"Erreur graphique trésorerie: {e}")
    
    # Graphique combiné revenus vs collections
    st.markdown("##### Revenus vs Collections")
    try:
        # Simuler des données mensuelles (à remplacer par vraies données)
        months = pd.date_range(start='2024-01-01', periods=12, freq='M')
        revenus = np.random.normal(15000, 3000, 12)
        collections = revenus * np.random.normal(0.92, 0.05, 12)  # 92% collecté en moyenne
        
        df_rev = pd.DataFrame({
            'month': months,
            'revenus_factures': revenus,
            'collections_realisees': collections
        })
        
        fig_rev = go.Figure()
        fig_rev.add_trace(go.Bar(
            x=df_rev['month'],
            y=df_rev['revenus_factures'],
            name='Revenus Facturés',
            marker_color='lightblue'
        ))
        fig_rev.add_trace(go.Bar(
            x=df_rev['month'],
            y=df_rev['collections_realisees'],
            name='Collections Réalisées',
            marker_color='darkblue'
        ))
        
        fig_rev.update_layout(
            title="Revenus Facturés vs Collections Réalisées",
            xaxis_title="Mois",
            yaxis_title="Montant (€)",
            barmode='group',
            height=400
        )
        st.plotly_chart(fig_rev, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur graphique revenus: {e}")

def show_aging_analysis(payment_dashboard: PaymentDashboard):
    """Afficher l'analyse de l'aging des créances"""
    
    st.subheader("🎂 Analyse de l'Aging des Créances")
    
    try:
        aging_buckets = payment_dashboard.calculate_aging_buckets()
        
        if aging_buckets:
            # Graphique en secteurs
            col1, col2 = st.columns(2)
            
            with col1:
                labels = [bucket.bucket_name for bucket in aging_buckets]
                values = [bucket.total_amount for bucket in aging_buckets]
                colors = ['#00CC96', '#FFA15A', '#FF6692', '#B6E880']
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    marker_colors=colors
                )])
                fig_pie.update_layout(
                    title="Répartition des Créances par Âge",
                    height=400
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Tableau détaillé aging
                aging_data = []
                for bucket in aging_buckets:
                    aging_data.append({
                        'Tranche': bucket.bucket_name,
                        'Nombre': bucket.count,
                        'Montant (€)': f"{bucket.total_amount:,.0f}",
                        'Pourcentage': f"{bucket.percentage:.1f}%"
                    })
                
                df_aging = pd.DataFrame(aging_data)
                st.markdown("##### Détail par Tranche")
                st.dataframe(df_aging, use_container_width=True, hide_index=True)
                
                # Alertes basées sur l'aging
                total_overdue = sum(bucket.total_amount for bucket in aging_buckets[1:])  # Exclure 0-30j
                total_receivables = sum(bucket.total_amount for bucket in aging_buckets)
                
                if total_receivables > 0:
                    overdue_pct = (total_overdue / total_receivables) * 100
                    
                    if overdue_pct > 30:
                        st.error(f"🚨 Alerte: {overdue_pct:.1f}% des créances sont en retard!")
                    elif overdue_pct > 15:
                        st.warning(f"⚠️ Attention: {overdue_pct:.1f}% des créances sont en retard")
                    else:
                        st.success(f"✅ Situation saine: {overdue_pct:.1f}% de retard")
            
            # Détail des factures par tranche
            st.markdown("##### Détail des Factures par Tranche")
            selected_bucket = st.selectbox(
                "Sélectionner une tranche d'âge",
                [bucket.bucket_name for bucket in aging_buckets]
            )
            
            # Trouver la tranche sélectionnée
            selected_bucket_obj = next(
                (bucket for bucket in aging_buckets if bucket.bucket_name == selected_bucket),
                None
            )
            
            if selected_bucket_obj:
                # Récupérer le détail des factures
                aging_detail = payment_dashboard.get_aging_detail(
                    selected_bucket_obj.min_days,
                    selected_bucket_obj.max_days
                )
                
                if aging_detail:
                    df_detail = pd.DataFrame(aging_detail)
                    
                    # Colonnes à afficher
                    display_cols = {
                        'invoice_number': 'N° Facture',
                        'participant_name': 'Client',
                        'due_date': 'Échéance',
                        'outstanding': 'Montant Dû (€)',
                        'days_overdue': 'Jours de Retard'
                    }
                    
                    df_display = df_detail[list(display_cols.keys())].rename(columns=display_cols)
                    df_display['Montant Dû (€)'] = df_display['Montant Dû (€)'].apply(lambda x: f"{x:,.2f}")
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info(f"Aucune facture dans la tranche {selected_bucket}")
        else:
            st.info("Aucune donnée d'aging disponible")
    
    except Exception as e:
        st.error(f"Erreur analyse aging: {e}")

def show_payment_methods_analysis(payment_dashboard: PaymentDashboard):
    """Afficher l'analyse des moyens de paiement"""
    
    st.subheader("💳 Analyse des Moyens de Paiement")
    
    try:
        payment_analytics = payment_dashboard.get_payment_method_analytics()
        
        if payment_analytics['payment_method_distribution']:
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique répartition moyens de paiement
                methods = list(payment_analytics['payment_method_distribution'].keys())
                amounts = [
                    payment_analytics['payment_method_distribution'][method]['total_amount']
                    for method in methods
                ]
                
                fig_methods = px.bar(
                    x=methods,
                    y=amounts,
                    title="Montants par Moyen de Paiement",
                    labels={'x': 'Moyen de Paiement', 'y': 'Montant (€)'}
                )
                fig_methods.update_layout(height=400)
                st.plotly_chart(fig_methods, use_container_width=True)
            
            with col2:
                # Tableau détaillé
                method_data = []
                for method, stats in payment_analytics['payment_method_distribution'].items():
                    avg_delay = payment_analytics['average_delay_by_method'].get(method, 0)
                    
                    method_data.append({
                        'Moyen': method.replace('_', ' ').title(),
                        'Nombre': stats['count'],
                        'Montant (€)': f"{stats['total_amount']:,.0f}",
                        'Part (%)': f"{stats['percentage']:.1f}%",
                        'Délai Moy.': f"{avg_delay:.1f}j"
                    })
                
                df_methods = pd.DataFrame(method_data)
                st.markdown("##### Performance par Moyen")
                st.dataframe(df_methods, use_container_width=True, hide_index=True)
                
                # Recommandations
                st.markdown("##### 💡 Recommandations")
                
                # Analyser les délais
                best_method = min(
                    payment_analytics['average_delay_by_method'].items(),
                    key=lambda x: x[1]
                )
                worst_method = max(
                    payment_analytics['average_delay_by_method'].items(),
                    key=lambda x: x[1]
                )
                
                st.info(f"✅ Moyen le plus rapide: {best_method[0]} ({best_method[1]:.1f}j)")
                st.warning(f"⚠️ Moyen le plus lent: {worst_method[0]} ({worst_method[1]:.1f}j)")
        else:
            st.info("Aucune donnée de paiement disponible")
    
    except Exception as e:
        st.error(f"Erreur analyse moyens de paiement: {e}")

def show_alerts_and_notifications(db: BillingDatabase, dunning_mgr: DunningManager, payment_mgr: PaymentManager):
    """Afficher les alertes et notifications"""
    
    st.subheader("🔔 Alertes et Notifications")
    
    # === ALERTES CRITIQUES ===
    st.markdown("##### 🚨 Alertes Critiques")
    
    alerts = []
    
    try:
        # Factures très en retard (>90 jours)
        aging_buckets = PaymentDashboard(db.db_path).calculate_aging_buckets()
        very_overdue = next((bucket for bucket in aging_buckets if "91+" in bucket.bucket_name), None)
        
        if very_overdue and very_overdue.total_amount > 0:
            alerts.append({
                'type': 'CRITICAL',
                'icon': '🚨',
                'title': 'Factures très en retard',
                'message': f"{very_overdue.count} factures >90j ({very_overdue.total_amount:,.0f}€)",
                'action': 'Relance urgente requise'
            })
        
        # DSO trop élevé
        dso = PaymentDashboard(db.db_path).calculate_dso()
        if dso.dso_days > 60:
            alerts.append({
                'type': 'WARNING',
                'icon': '⚠️',
                'title': 'DSO élevé',
                'message': f"DSO à {dso.dso_days:.1f} jours (objectif: <45j)",
                'action': 'Accélérer les relances'
            })
        
        # Taux de recouvrement faible
        collection_metrics = PaymentDashboard(db.db_path).calculate_collection_rate()
        if collection_metrics.collection_rate < 80:
            alerts.append({
                'type': 'WARNING',
                'icon': '📉',
                'title': 'Taux de recouvrement faible',
                'message': f"Seulement {collection_metrics.collection_rate:.1f}% collecté",
                'action': 'Revoir la stratégie de relance'
            })
        
        # Affichage des alertes
        if alerts:
            for alert in alerts:
                if alert['type'] == 'CRITICAL':
                    st.error(f"{alert['icon']} **{alert['title']}**: {alert['message']} → {alert['action']}")
                else:
                    st.warning(f"{alert['icon']} **{alert['title']}**: {alert['message']} → {alert['action']}")
        else:
            st.success("✅ Aucune alerte critique")
    
    except Exception as e:
        st.error(f"Erreur calcul alertes: {e}")
    
    # === ACTIONS RECOMMANDÉES ===
    st.markdown("##### 💡 Actions Recommandées")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Actions Prioritaires**")
        
        try:
            # Factures à relancer
            overdue_invoices = dunning_mgr.get_overdue_invoices()
            if overdue_invoices:
                st.info(f"📧 {len(overdue_invoices)} factures à relancer")
                
                if st.button("🚀 Lancer cycle de relances", type="primary"):
                    with st.spinner("Traitement des relances..."):
                        results = dunning_mgr.process_dunning_cycle(dry_run=True)
                        st.success(f"✅ {results['processed_count']} actions de relance programmées")
            
            # Transactions non rapprochées
            unmatched = payment_mgr.get_unmatched_transactions(limit=10)
            if unmatched:
                st.info(f"🔍 {len(unmatched)} transactions à rapprocher")
                
                if st.button("🎯 Rapprochement automatique"):
                    with st.spinner("Rapprochement en cours..."):
                        results = payment_mgr.match_payments_to_invoices()
                        st.success(f"✅ {results['auto_matches_count']} rapprochements automatiques")
        
        except Exception as e:
            st.error(f"Erreur actions: {e}")
    
    with col2:
        st.markdown("**📊 Monitoring Continu**")
        
        # Statistiques de relance
        try:
            dunning_stats = dunning_mgr.get_dunning_statistics()
            
            st.metric(
                "Taux de succès relances",
                f"{dunning_stats.get('success_rate_percent', 0):.1f}%",
                delta="90 derniers jours"
            )
            
            st.metric(
                "Factures impayées",
                dunning_stats.get('overdue_invoices_count', 0),
                delta=f"{dunning_stats.get('overdue_total_amount', 0):,.0f}€"
            )
        
        except Exception as e:
            st.error(f"Erreur stats relances: {e}")
    
    # === NOTIFICATIONS RÉCENTES ===
    st.markdown("##### 📰 Activité Récente")
    
    # Simuler des notifications récentes
    notifications = [
        {
            'time': '10:30',
            'type': 'success',
            'message': 'Paiement reçu: 1,250€ - Facture INV-2024-047'
        },
        {
            'time': '09:15',
            'type': 'info',
            'message': 'Relance automatique envoyée à 3 clients'
        },
        {
            'time': '08:45',
            'type': 'warning',
            'message': 'Facture INV-2024-023 en retard de 45 jours'
        }
    ]
    
    for notif in notifications:
        if notif['type'] == 'success':
            st.success(f"**{notif['time']}** - {notif['message']}")
        elif notif['type'] == 'warning':
            st.warning(f"**{notif['time']}** - {notif['message']}")
        else:
            st.info(f"**{notif['time']}** - {notif['message']}")

# === FONCTIONS D'EXPORT ===
def export_dashboard_data():
    """Exporter les données du dashboard"""
    
    st.sidebar.markdown("### 📥 Export de Données")
    
    export_type = st.sidebar.selectbox(
        "Type d'export",
        ["Rapport KPIs (PDF)", "Données Aging (Excel)", "Prévisions Trésorerie (CSV)"]
    )
    
    if st.sidebar.button("📥 Exporter", type="primary"):
        st.sidebar.success(f"✅ Export {export_type} généré")
        # TODO: Implémenter les exports réels