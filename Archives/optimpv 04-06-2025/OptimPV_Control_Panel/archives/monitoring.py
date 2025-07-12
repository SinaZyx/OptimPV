# panel/monitoring.py
"""
Module de monitoring et visualisation des logs
Interface Streamlit pour surveillance système
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import time

from utils.logger import SecureLogger
from process.process_monitor import ProcessMonitor
from config.constants import LOGS_DIR


class MonitoringModule:
    """Interface de monitoring système et logs"""
    
    def __init__(self, security_core):
        self.security_core = security_core
        self.logger = SecureLogger()
        self.process_monitor = ProcessMonitor()
        
    def render(self):
        """Afficher l'interface de monitoring"""
        st.markdown("### 📊 Monitoring & Logs")
        
        # Tabs principales
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Vue d'ensemble",
            "Logs Temps Réel", 
            "Métriques Système",
            "Analyse Sécurité",
            "Rapports"
        ])
        
        with tab1:
            self._render_overview()
        
        with tab2:
            self._render_realtime_logs()
        
        with tab3:
            self._render_system_metrics()
        
        with tab4:
            self._render_security_analysis()
        
        with tab5:
            self._render_reports()
    
    def _render_overview(self):
        """Vue d'ensemble du système"""
        st.markdown("#### 🏠 Vue d'Ensemble")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Uptime système
            uptime = datetime.now() - datetime.fromtimestamp(
                st.session_state.get('start_time', 0)
            )
            st.metric("Uptime Système", f"{uptime.days}j {uptime.seconds//3600}h")
        
        with col2:
            # Événements sécurité 24h
            recent_events = self._count_recent_security_events(hours=24)
            st.metric(
                "Événements Sécurité (24h)", 
                recent_events,
                delta=f"{recent_events - 10:+d}" if recent_events > 10 else "Normal"
            )
        
        with col3:
            # Santé système
            health_score = self._calculate_system_health()
            st.metric(
                "Santé Système",
                f"{health_score}%",
                delta="Bon" if health_score > 80 else "Attention"
            )
        
        with col4:
            # Alertes actives
            active_alerts = self._get_active_alerts()
            st.metric("Alertes Actives", len(active_alerts))
        
        # Graphique timeline événements
        st.markdown("---")
        st.markdown("**📈 Timeline des Événements (7 derniers jours)**")
        
        timeline_data = self._get_event_timeline(days=7)
        if timeline_data:
            fig = px.line(
                timeline_data,
                x='timestamp',
                y='count',
                color='type',
                title="Événements par Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible")
        
        # Alertes récentes
        st.markdown("---")
        st.markdown("**🚨 Alertes Récentes**")
        
        if active_alerts:
            for alert in active_alerts[:5]:
                alert_color = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠', 
                    'MEDIUM': '🟡',
                    'LOW': '🔵'
                }.get(alert['severity'], '⚪')
                
                with st.expander(f"{alert_color} {alert['type']} - {alert['timestamp']}"):
                    st.json(alert['details'])
        else:
            st.success("✅ Aucune alerte active")
    
    def _render_realtime_logs(self):
        """Affichage des logs en temps réel"""
        st.markdown("#### 📜 Logs Temps Réel")
        
        # Contrôles
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            log_level = st.selectbox(
                "Niveau",
                ["TOUS", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                index=2
            )
        
        with col2:
            log_type = st.selectbox(
                "Type",
                ["TOUS", "SECURITY", "SYSTEM", "APPLICATION", "NETWORK"]
            )
        
        with col3:
            auto_refresh = st.checkbox("Auto-refresh", value=True)
            
        with col4:
            if st.button("🔄 Actualiser"):
                st.rerun()
        
        # Zone de logs
        log_container = st.container()
        
        with log_container:
            # Récupérer logs récents
            recent_logs = self.logger.get_recent_logs(100)
            
            # Filtrer
            filtered_logs = self._filter_logs(recent_logs, log_level, log_type)
            
            # Afficher
            if filtered_logs:
                # Format tableau
                log_data = []
                for log in filtered_logs:
                    log_data.append({
                        'Timestamp': log['timestamp'],
                        'Level': log.get('level', log.get('severity', 'INFO')),
                        'Type': log['type'],
                        'Message': str(log.get('details', {}))[:100] + '...'
                    })
                
                df = pd.DataFrame(log_data)
                
                # Styling conditionnel
                def highlight_severity(row):
                    colors = {
                        'CRITICAL': 'background-color: #ff4444',
                        'ERROR': 'background-color: #ff6666',
                        'WARNING': 'background-color: #ffaa44',
                        'INFO': '',
                        'DEBUG': 'opacity: 0.7'
                    }
                    return [colors.get(row['Level'], '')] * len(row)
                
                styled_df = df.style.apply(highlight_severity, axis=1)
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    height=400
                )
                
                # Détails au clic
                selected_indices = st.multiselect(
                    "Voir détails des logs:",
                    range(len(filtered_logs)),
                    format_func=lambda i: f"Log {i+1}: {filtered_logs[i]['type']}"
                )
                
                for idx in selected_indices:
                    with st.expander(f"Détails Log {idx+1}"):
                        st.json(filtered_logs[idx])
            else:
                st.info("Aucun log correspondant aux critères")
        
        # Auto-refresh
        if auto_refresh:
            time.sleep(5)
            st.rerun()
    
    def _render_system_metrics(self):
        """Métriques système détaillées"""
        st.markdown("#### 📊 Métriques Système")
        
        # Sélection période
        col1, col2 = st.columns([3, 1])
        
        with col1:
            time_range = st.select_slider(
                "Période",
                options=["1h", "6h", "24h", "7j", "30j"],
                value="24h"
            )
        
        with col2:
            if st.button("🔄 Actualiser Métriques"):
                st.rerun()
        
        # Conversion période
        periods = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(days=1),
            "7j": timedelta(days=7),
            "30j": timedelta(days=30)
        }
        period = periods[time_range]
        
        # Graphiques métriques
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU
            st.markdown("**🖥️ Utilisation CPU**")
            cpu_data = self._get_metric_history('cpu', period)
            
            if cpu_data:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=cpu_data['timestamp'],
                    y=cpu_data['value'],
                    mode='lines',
                    name='CPU %',
                    line=dict(color='#4a9eff')
                ))
                fig.update_layout(
                    height=300,
                    yaxis_range=[0, 100],
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Mémoire
            st.markdown("**💾 Utilisation Mémoire**")
            mem_data = self._get_metric_history('memory', period)
            
            if mem_data:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=mem_data['timestamp'],
                    y=mem_data['value'],
                    mode='lines',
                    name='RAM %',
                    line=dict(color='#ff6b6b')
                ))
                fig.update_layout(
                    height=300,
                    yaxis_range=[0, 100],
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Métriques détaillées
        st.markdown("---")
        st.markdown("**📈 Métriques Détaillées**")
        
        # Tabs pour différentes catégories
        metric_tabs = st.tabs(["Réseau", "Disque", "Processus", "Température"])
        
        with metric_tabs[0]:
            self._render_network_metrics(period)
        
        with metric_tabs[1]:
            self._render_disk_metrics(period)
        
        with metric_tabs[2]:
            self._render_process_metrics()
        
        with metric_tabs[3]:
            self._render_temperature_metrics()
    
    def _render_security_analysis(self):
        """Analyse de sécurité approfondie"""
        st.markdown("#### 🔍 Analyse de Sécurité")
        
        # Filtres temporels
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analysis_type = st.selectbox(
                "Type d'analyse",
                ["Tentatives d'accès", "Anomalies", "Vulnérabilités", "Audit complet"]
            )
        
        with col2:
            date_range = st.date_input(
                "Période",
                value=(datetime.now().date() - timedelta(days=7), datetime.now().date())
            )
        
        with col3:
            severity_filter = st.multiselect(
                "Sévérité",
                ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                default=["CRITICAL", "HIGH"]
            )
        
        # Lancer analyse
        if st.button("🔍 Lancer Analyse", type="primary"):
            with st.spinner("Analyse en cours..."):
                results = self._perform_security_analysis(
                    analysis_type,
                    date_range,
                    severity_filter
                )
                
                if results:
                    # Résumé
                    st.markdown("---")
                    st.markdown("**📊 Résumé de l'Analyse**")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Événements analysés", results['total_events'])
                    
                    with col2:
                        st.metric("Anomalies détectées", results['anomalies'])
                    
                    with col3:
                        risk_score = results['risk_score']
                        risk_level = "Faible" if risk_score < 30 else "Moyen" if risk_score < 70 else "Élevé"
                        st.metric("Score de risque", f"{risk_score}/100", delta=risk_level)
                    
                    # Détails
                    st.markdown("---")
                    st.markdown("**🔎 Détails de l'Analyse**")
                    
                    # Graphique distribution
                    if results['distribution']:
                        fig = px.pie(
                            values=list(results['distribution'].values()),
                            names=list(results['distribution'].keys()),
                            title="Distribution des Événements"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Recommandations
                    if results['recommendations']:
                        st.markdown("**💡 Recommandations**")
                        for rec in results['recommendations']:
                            st.warning(f"• {rec}")
                    
                    # Export
                    if st.button("📥 Exporter Rapport"):
                        report = self._generate_security_report(results)
                        st.download_button(
                            "Télécharger",
                            data=report,
                            file_name=f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
    
    def _render_reports(self):
        """Génération de rapports"""
        st.markdown("#### 📑 Rapports")
        
        # Type de rapport
        report_type = st.selectbox(
            "Type de rapport",
            [
                "Rapport quotidien",
                "Rapport hebdomadaire", 
                "Rapport mensuel",
                "Rapport d'incident",
                "Rapport personnalisé"
            ]
        )
        
        # Configuration rapport
        with st.expander("⚙️ Configuration du Rapport", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                include_sections = st.multiselect(
                    "Sections à inclure",
                    [
                        "Résumé exécutif",
                        "Événements sécurité",
                        "Métriques système",
                        "Logs détaillés",
                        "Graphiques",
                        "Recommandations"
                    ],
                    default=["Résumé exécutif", "Événements sécurité", "Métriques système"]
                )
            
            with col2:
                report_format = st.radio(
                    "Format",
                    ["PDF", "JSON", "CSV", "HTML"]
                )
                
                include_sensitive = st.checkbox(
                    "Inclure données sensibles",
                    value=False,
                    help="⚠️ Nécessite privilèges admin"
                )
        
        # Génération
        if st.button("📊 Générer Rapport", type="primary"):
            with st.spinner("Génération en cours..."):
                try:
                    report_data = self._generate_report(
                        report_type,
                        include_sections,
                        include_sensitive
                    )
                    
                    if report_data:
                        st.success("✅ Rapport généré avec succès!")
                        
                        # Aperçu
                        with st.expander("👁️ Aperçu du Rapport"):
                            if report_format == "JSON":
                                st.json(report_data)
                            else:
                                st.text(str(report_data)[:500] + "...")
                        
                        # Téléchargement
                        file_extension = report_format.lower()
                        filename = f"{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
                        
                        st.download_button(
                            "📥 Télécharger Rapport",
                            data=self._format_report(report_data, report_format),
                            file_name=filename,
                            mime=self._get_mime_type(report_format)
                        )
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
        
        # Rapports programmés
        st.markdown("---")
        st.markdown("**📅 Rapports Programmés**")
        
        scheduled_reports = self._get_scheduled_reports()
        
        if scheduled_reports:
            for report in scheduled_reports:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.text(report['name'])
                
                with col2:
                    st.caption(report['schedule'])
                
                with col3:
                    st.caption(f"Prochain: {report['next_run']}")
                
                with col4:
                    if st.button("🗑️", key=f"del_report_{report['id']}"):
                        self._delete_scheduled_report(report['id'])
                        st.rerun()
        else:
            st.info("Aucun rapport programmé")
        
        # Ajouter rapport programmé
        if st.checkbox("➕ Programmer un nouveau rapport"):
            self._render_schedule_report_form()
    
    # Méthodes helper
    
    def _count_recent_security_events(self, hours: int) -> int:
        """Compter événements sécurité récents"""
        since = datetime.now() - timedelta(hours=hours)
        events = self.logger.search_logs(since, datetime.now())
        return len([e for e in events if e.get('type', '').startswith('SECURITY')])
    
    def _calculate_system_health(self) -> int:
        """Calculer score de santé système"""
        score = 100
        
        # Facteurs négatifs
        try:
            import psutil
            
            # CPU élevé
            if psutil.cpu_percent(interval=1) > 80:
                score -= 20
            
            # RAM élevée
            if psutil.virtual_memory().percent > 85:
                score -= 15
            
            # Disque plein
            if psutil.disk_usage('/').percent > 90:
                score -= 25
            
            # Événements sécurité
            security_events = self._count_recent_security_events(1)
            if security_events > 10:
                score -= min(security_events, 30)
                
        except:
            pass
        
        return max(score, 0)
    
    def _get_active_alerts(self) -> List[Dict]:
        """Obtenir alertes actives"""
        # Simuler pour démo
        return []
    
    def _get_event_timeline(self, days: int) -> pd.DataFrame:
        """Obtenir timeline événements"""
        # TODO: Implémenter agrégation réelle
        return None
    
    def _filter_logs(self, logs: List[Dict], level: str, log_type: str) -> List[Dict]:
        """Filtrer logs selon critères"""
        filtered = logs
        
        if level != "TOUS":
            filtered = [l for l in filtered if l.get('level') == level or l.get('severity') == level]
        
        if log_type != "TOUS":
            filtered = [l for l in filtered if log_type in l.get('type', '')]
        
        return filtered
    
    def _get_metric_history(self, metric: str, period: timedelta) -> Dict:
        """Obtenir historique métrique"""
        # TODO: Implémenter collecte métriques réelle
        return None
    
    def _render_network_metrics(self, period: timedelta):
        """Afficher métriques réseau"""
        st.info("Métriques réseau à implémenter")
    
    def _render_disk_metrics(self, period: timedelta):
        """Afficher métriques disque"""
        st.info("Métriques disque à implémenter")
    
    def _render_process_metrics(self):
        """Afficher métriques processus"""
        st.info("Métriques processus à implémenter")
    
    def _render_temperature_metrics(self):
        """Afficher températures système"""
        st.info("Métriques température à implémenter")
    
    def _perform_security_analysis(self, analysis_type: str, date_range: tuple, 
                                  severity_filter: List[str]) -> Dict:
        """Effectuer analyse sécurité"""
        # TODO: Implémenter analyse réelle
        return {
            'total_events': 1234,
            'anomalies': 12,
            'risk_score': 45,
            'distribution': {
                'AUTH_SUCCESS': 890,
                'AUTH_FAILURE': 234,
                'SUSPICIOUS': 89,
                'CRITICAL': 21
            },
            'recommendations': [
                "Mettre à jour les règles de pare-feu",
                "Revoir les permissions d'accès",
                "Activer l'authentification 2FA"
            ]
        }
    
    def _generate_security_report(self, results: Dict) -> str:
        """Générer rapport sécurité"""
        return json.dumps(results, indent=2)
    
    def _generate_report(self, report_type: str, sections: List[str], 
                        include_sensitive: bool) -> Dict:
        """Générer rapport complet"""
        report = {
            'type': report_type,
            'generated': datetime.now().isoformat(),
            'sections': {}
        }
        
        # TODO: Implémenter génération sections
        
        return report
    
    def _format_report(self, data: Dict, format: str) -> bytes:
        """Formater rapport pour export"""
        if format == "JSON":
            return json.dumps(data, indent=2).encode()
        # TODO: Implémenter autres formats
        return str(data).encode()
    
    def _get_mime_type(self, format: str) -> str:
        """Obtenir MIME type pour format"""
        mime_types = {
            'JSON': 'application/json',
            'CSV': 'text/csv',
            'PDF': 'application/pdf',
            'HTML': 'text/html'
        }
        return mime_types.get(format, 'text/plain')
    
    def _get_scheduled_reports(self) -> List[Dict]:
        """Obtenir rapports programmés"""
        # TODO: Implémenter
        return []
    
    def _delete_scheduled_report(self, report_id: str):
        """Supprimer rapport programmé"""
        pass
    
    def _render_schedule_report_form(self):
        """Formulaire pour programmer rapport"""
        st.info("Fonctionnalité à implémenter")# Composant UI pour le monitoring et les logs 