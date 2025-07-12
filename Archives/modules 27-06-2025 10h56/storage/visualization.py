"""
Visualization - Visualisations et graphiques pour la comparaison de projets
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ComparisonVisualization:
    """Visualisations pour la comparaison de projets"""
    
    def __init__(self, storage_module):
        self.storage = storage_module
    
    def _show_synthesis_comparison(self, comparison_data):
        """Affiche la synthèse de comparaison"""
        st.subheader("📈 Synthèse de la comparaison")
        
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        
        # Métriques principales
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### 📁 {manifest1['name']}")
            self._show_project_status_mini(manifest1.get('completeness', {}).get('components', {}))
            
            # Informations du projet
            st.markdown(f"**Créé:** {manifest1.get('created_at', 'N/A')[:10]}")
            st.markdown(f"**Taille:** {manifest1.get('data_size', {}).get('total_size_mb', 0):.1f} MB")
            st.markdown(f"**Complétude:** {manifest1.get('completeness', {}).get('score', 0):.1f}%")
        
        with col2:
            st.markdown(f"### 📁 {manifest2['name']}")
            self._show_project_status_mini(manifest2.get('completeness', {}).get('components', {}))
            
            # Informations du projet
            st.markdown(f"**Créé:** {manifest2.get('created_at', 'N/A')[:10]}")
            st.markdown(f"**Taille:** {manifest2.get('data_size', {}).get('total_size_mb', 0):.1f} MB")
            st.markdown(f"**Complétude:** {manifest2.get('completeness', {}).get('score', 0):.1f}%")
        
        # Graphique radar de comparaison
        self._show_radar_comparison(comparison_data)
        
        # Conclusion automatique
        self._generate_automatic_conclusion(comparison_data)
    
    def _show_project_status_mini(self, components):
        """Affiche un mini statut de projet"""
        module_mapping = {
            'data_imported': ('📊', 'Données'),
            'config_set': ('⚙️', 'Config'),
            'scenarios_defined': ('🎭', 'Scénarios'),
            'economic_analysis': ('💰', 'Économie'),
            'optimization_done': ('⚡', 'Optimisation'),
            'monte_carlo_done': ('🎲', 'Monte Carlo')
        }
        
        status_html = ""
        for key, (icon, label) in module_mapping.items():
            status = components.get(key, False)
            color = "#28a745" if status else "#6c757d"
            status_html += f'<span style="color: {color}; margin-right: 8px;" title="{label}">{icon}</span>'
        
        st.markdown(status_html, unsafe_allow_html=True)
    
    def _show_radar_comparison(self, comparison_data):
        """Affiche un graphique radar de comparaison"""
        st.subheader("🎯 Comparaison radar")
        
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        
        # Définir les métriques pour le radar
        metrics = {
            'Complétude': [
                manifest1.get('completeness', {}).get('score', 0),
                manifest2.get('completeness', {}).get('score', 0)
            ],
            'Qualité': [
                manifest1.get('validation', {}).get('data_quality_score', 0),
                manifest2.get('validation', {}).get('data_quality_score', 0)
            ],
            'Données': [
                100 if manifest1.get('completeness', {}).get('components', {}).get('data_imported', False) else 0,
                100 if manifest2.get('completeness', {}).get('components', {}).get('data_imported', False) else 0
            ],
            'Configuration': [
                100 if manifest1.get('completeness', {}).get('components', {}).get('config_set', False) else 0,
                100 if manifest2.get('completeness', {}).get('components', {}).get('config_set', False) else 0
            ],
            'Économie': [
                100 if manifest1.get('completeness', {}).get('components', {}).get('economic_analysis', False) else 0,
                100 if manifest2.get('completeness', {}).get('components', {}).get('economic_analysis', False) else 0
            ],
            'Optimisation': [
                100 if manifest1.get('completeness', {}).get('components', {}).get('optimization_done', False) else 0,
                100 if manifest2.get('completeness', {}).get('components', {}).get('optimization_done', False) else 0
            ]
        }
        
        # Créer le graphique radar
        fig = go.Figure()
        
        categories = list(metrics.keys())
        values1 = [metrics[cat][0] for cat in categories]
        values2 = [metrics[cat][1] for cat in categories]
        
        # Ajouter les lignes du radar
        fig.add_trace(go.Scatterpolar(
            r=values1 + [values1[0]],  # Fermer la forme
            theta=categories + [categories[0]],
            fill='toself',
            name=manifest1['name'],
            line_color='blue'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=values2 + [values2[0]],  # Fermer la forme
            theta=categories + [categories[0]],
            fill='toself',
            name=manifest2['name'],
            line_color='red'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Comparaison des caractéristiques des projets",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _generate_automatic_conclusion(self, comparison_data):
        """Génère une conclusion automatique de la comparaison"""
        st.subheader("🎯 Conclusion automatique")
        
        manifest1 = comparison_data['manifest1']
        manifest2 = comparison_data['manifest2']
        key_differences = comparison_data['key_differences']
        
        conclusions = []
        
        # Analyser la complétude
        score1 = manifest1.get('completeness', {}).get('score', 0)
        score2 = manifest2.get('completeness', {}).get('score', 0)
        
        if abs(score1 - score2) > 10:
            better_project = manifest1['name'] if score1 > score2 else manifest2['name']
            conclusions.append(f"📊 **{better_project}** est plus complet ({max(score1, score2):.1f}% vs {min(score1, score2):.1f}%)")
        
        # Analyser les changements de configuration majeurs
        config_changes = key_differences.get('config_changes', [])
        major_changes = [c for c in config_changes if c['parameter'] in ['capex_scenario', 'puissance_kwc_installee', 'duree_ppa']]
        
        if major_changes:
            conclusions.append(f"⚙️ **{len(major_changes)} changements majeurs** de configuration détectés")
            for change in major_changes[:3]:  # Limiter à 3 pour éviter le spam
                param = change['parameter'].replace('_', ' ').title()
                val1 = change['project1']
                val2 = change['project2']
                conclusions.append(f"   - {param}: {val1} → {val2}")
        
        # Analyser les performances
        performance_delta = key_differences.get('performance_delta', {})
        if performance_delta:
            for metric, data in performance_delta.items():
                if data.get('delta_percent') and abs(data['delta_percent']) > 5:
                    direction = "amélioration" if data['delta_percent'] > 0 else "dégradation"
                    conclusions.append(f"💰 **{metric}**: {direction} de {abs(data['delta_percent']):.1f}%")
        
        # Afficher les conclusions
        if conclusions:
            for conclusion in conclusions:
                st.markdown(f"- {conclusion}")
        else:
            st.info("Les projets sont très similaires, aucune différence majeure détectée.")
    
    def _show_config_comparison(self, comparison_data):
        """Affiche la comparaison de configuration"""
        st.subheader("⚙️ Comparaison de configuration")
        
        config1 = comparison_data['config1']
        config2 = comparison_data['config2']
        
        if not config1 and not config2:
            st.warning("Aucune configuration disponible pour la comparaison")
            return
        
        # Créer un DataFrame pour la comparaison
        all_keys = set(config1.keys()) | set(config2.keys())
        
        comparison_data_list = []
        for key in sorted(all_keys):
            val1 = config1.get(key, "N/A")
            val2 = config2.get(key, "N/A")
            
            # Déterminer si c'est différent
            is_different = self.storage.comparison._is_significantly_different(val1, val2, key)
            
            comparison_data_list.append({
                'Paramètre': key.replace('_', ' ').title(),
                'Projet 1': val1,
                'Projet 2': val2,
                'Différent': is_different
            })
        
        if comparison_data_list:
            df = pd.DataFrame(comparison_data_list)
            
            # Styliser le tableau
            def highlight_differences(row):
                if row['Différent']:
                    return ['background-color: #ffeeee'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = df.style.apply(highlight_differences, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # Statistiques
            different_count = sum(item['Différent'] for item in comparison_data_list)
            st.info(f"📊 {different_count} paramètres différents sur {len(comparison_data_list)} total")
    
    def _show_economic_comparison(self, comparison_data):
        """Affiche la comparaison économique"""
        st.subheader("💰 Comparaison économique")
        
        economic1 = comparison_data['economic1']
        economic2 = comparison_data['economic2']
        
        if not economic1 and not economic2:
            st.warning("Aucun résultat économique disponible pour la comparaison")
            return
        
        # Prendre le premier scénario de chaque projet
        scenario1 = list(economic1.keys())[0] if economic1 else None
        scenario2 = list(economic2.keys())[0] if economic2 else None
        
        if not scenario1 or not scenario2:
            st.warning("Données économiques incomplètes")
            return
        
        results1 = economic1[scenario1]
        results2 = economic2[scenario2]
        
        # Afficher le tableau de comparaison détaillé
        self._show_detailed_economic_table(results1, results2, comparison_data)
        
        # Graphique de comparaison des données mensuelles si disponibles
        if 'monthly_data' in results1 and 'monthly_data' in results2:
            self._plot_monthly_data_comparison(results1['monthly_data'], results2['monthly_data'], comparison_data)
    
    def _plot_monthly_data_comparison(self, monthly_data1, monthly_data2, comparison_data):
        """Trace la comparaison des données mensuelles"""
        st.subheader("📈 Comparaison des flux mensuels")
        
        try:
            # Convertir en DataFrames si nécessaire
            if isinstance(monthly_data1, list):
                df1 = pd.DataFrame(monthly_data1)
                if 'Temps' in df1.columns:
                    df1['Temps'] = pd.to_datetime(df1['Temps'])
                    df1.set_index('Temps', inplace=True)
            else:
                df1 = monthly_data1
            
            if isinstance(monthly_data2, list):
                df2 = pd.DataFrame(monthly_data2)
                if 'Temps' in df2.columns:
                    df2['Temps'] = pd.to_datetime(df2['Temps'])
                    df2.set_index('Temps', inplace=True)
            else:
                df2 = monthly_data2
            
            # Sélectionner les métriques à comparer
            metrics_to_compare = ['Revenus_Total', 'FCFE', 'EBITDA']
            available_metrics = [m for m in metrics_to_compare if m in df1.columns and m in df2.columns]
            
            if not available_metrics:
                st.warning("Aucune métrique commune pour la comparaison mensuelle")
                return
            
            # Créer des sous-graphiques
            fig = make_subplots(
                rows=len(available_metrics), 
                cols=1,
                subplot_titles=available_metrics,
                shared_xaxes=True
            )
            
            colors = ['blue', 'red']
            names = [comparison_data['manifest1']['name'], comparison_data['manifest2']['name']]
            
            for i, metric in enumerate(available_metrics):
                # Projet 1
                fig.add_trace(
                    go.Scatter(
                        x=df1.index,
                        y=df1[metric],
                        name=f"{names[0]} - {metric}",
                        line=dict(color=colors[0]),
                        showlegend=(i == 0)
                    ),
                    row=i+1, col=1
                )
                
                # Projet 2
                fig.add_trace(
                    go.Scatter(
                        x=df2.index,
                        y=df2[metric],
                        name=f"{names[1]} - {metric}",
                        line=dict(color=colors[1]),
                        showlegend=(i == 0)
                    ),
                    row=i+1, col=1
                )
            
            fig.update_layout(
                height=300 * len(available_metrics),
                title="Comparaison des flux financiers mensuels"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du graphique mensuel: {e}")
            st.error("Erreur lors de la génération du graphique mensuel")
    
    def _show_detailed_economic_table(self, results1, results2, comparison_data):
        """Affiche un tableau détaillé de comparaison économique"""
        st.subheader("📊 Tableau de comparaison détaillé")
        
        # Métriques principales à comparer
        key_metrics = [
            ('VAN_Projet', 'VAN Projet (€)'),
            ('VAN_Fonds_Propres', 'VAN Fonds Propres (€)'),
            ('TRI_Projet', 'TRI Projet (%)'),
            ('TRI_Fonds_Propres', 'TRI Fonds Propres (%)'),
            ('Payback_Projet', 'Payback Projet (ans)'),
            ('Payback_Fonds_Propres', 'Payback Fonds Propres (ans)'),
            ('LCOE', 'LCOE (€/MWh)'),
            ('Investissement_Initial', 'Investissement Initial (€)'),
            ('Chiffre_Affaires_Total', 'CA Total (€)')
        ]
        
        comparison_table = []
        
        for key, label in key_metrics:
            val1 = results1.get(key, 'N/A')
            val2 = results2.get(key, 'N/A')
            
            # Calculer la différence
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff_abs = val2 - val1
                diff_pct = (diff_abs / val1 * 100) if val1 != 0 else None
                diff_str = f"{diff_abs:+,.0f} ({diff_pct:+.1f}%)" if diff_pct is not None else f"{diff_abs:+,.0f}"
            else:
                diff_str = "N/A"
            
            comparison_table.append({
                'Métrique': label,
                'Projet 1': f"{val1:,.0f}" if isinstance(val1, (int, float)) else str(val1),
                'Projet 2': f"{val2:,.0f}" if isinstance(val2, (int, float)) else str(val2),
                'Différence': diff_str
            })
        
        df_comparison = pd.DataFrame(comparison_table)
        
        # Styliser le tableau
        def highlight_row(row):
            if 'N/A' not in str(row['Différence']) and any(char in str(row['Différence']) for char in ['+', '-']):
                if '+' in str(row['Différence']):
                    return [''] * 3 + ['background-color: #d4edda']  # Vert pour amélioration
                else:
                    return [''] * 3 + ['background-color: #f8d7da']  # Rouge pour dégradation
            return [''] * len(row)
        
        styled_df = df_comparison.style.apply(highlight_row, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    
    def _show_optimization_comparison(self, comparison_data):
        """Affiche la comparaison d'optimisation"""
        st.subheader("⚡ Comparaison d'optimisation")
        
        optimization1 = comparison_data['optimization1']
        optimization2 = comparison_data['optimization2']
        
        if not optimization1 and not optimization2:
            st.warning("Aucun résultat d'optimisation disponible pour la comparaison")
            return
        
        # Afficher les métriques d'optimisation
        self._show_optimization_metrics(optimization1, optimization2, comparison_data)
        
        # Graphique des courbes d'optimisation si disponible
        self._plot_optimization_curves(optimization1, optimization2, comparison_data)
    
    def _plot_optimization_curves(self, opt_data1, opt_data2, comparison_data):
        """Trace les courbes d'optimisation"""
        try:
            # Prendre le premier scénario de chaque projet
            scenario1 = list(opt_data1.keys())[0] if opt_data1 else None
            scenario2 = list(opt_data2.keys())[0] if opt_data2 else None
            
            if not scenario1 or not scenario2:
                return
            
            data1 = opt_data1[scenario1]
            data2 = opt_data2[scenario2]
            
            # Vérifier si on a les données des prix testés
            if 'prix_testes' not in data1 or 'prix_testes' not in data2:
                st.info("Données d'optimisation détaillées non disponibles pour le graphique")
                return
            
            fig = go.Figure()
            
            # Courbe du projet 1
            fig.add_trace(go.Scatter(
                x=data1['prix_testes'],
                y=[point.get('VAN', 0) for point in data1.get('resultats_detailles', [])],
                mode='lines+markers',
                name=comparison_data['manifest1']['name'],
                line=dict(color='blue')
            ))
            
            # Courbe du projet 2
            fig.add_trace(go.Scatter(
                x=data2['prix_testes'],
                y=[point.get('VAN', 0) for point in data2.get('resultats_detailles', [])],
                mode='lines+markers',
                name=comparison_data['manifest2']['name'],
                line=dict(color='red')
            ))
            
            # Marquer les prix optimaux
            if 'prix_optimal' in data1:
                fig.add_vline(
                    x=data1['prix_optimal'],
                    line_dash="dash",
                    line_color="blue",
                    annotation_text=f"Optimal {comparison_data['manifest1']['name']}"
                )
            
            if 'prix_optimal' in data2:
                fig.add_vline(
                    x=data2['prix_optimal'],
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Optimal {comparison_data['manifest2']['name']}"
                )
            
            fig.update_layout(
                title="Courbes d'optimisation - VAN vs Prix de vente",
                xaxis_title="Prix de vente (€/MWh)",
                yaxis_title="VAN (€)",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des courbes d'optimisation: {e}")
            st.error("Erreur lors de la génération des courbes d'optimisation")
    
    def _show_optimization_metrics(self, opt_data1, opt_data2, comparison_data):
        """Affiche les métriques d'optimisation"""
        if not opt_data1 or not opt_data2:
            return
        
        # Prendre le premier scénario de chaque projet
        scenario1 = list(opt_data1.keys())[0]
        scenario2 = list(opt_data2.keys())[0]
        
        data1 = opt_data1[scenario1]
        data2 = opt_data2[scenario2]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {comparison_data['manifest1']['name']}")
            st.metric("Prix optimal", f"{data1.get('prix_optimal', 'N/A')} €/MWh")
            indicateurs1 = data1.get('indicateurs_optimaux', {})
            st.metric("VAN optimal", f"{indicateurs1.get('VAN', 'N/A'):,} €" if isinstance(indicateurs1.get('VAN'), (int, float)) else "N/A")
            st.metric("TRI optimal", f"{indicateurs1.get('TRI', 'N/A')} %" if isinstance(indicateurs1.get('TRI'), (int, float)) else "N/A")
        
        with col2:
            st.markdown(f"### {comparison_data['manifest2']['name']}")
            st.metric("Prix optimal", f"{data2.get('prix_optimal', 'N/A')} €/MWh")
            indicateurs2 = data2.get('indicateurs_optimaux', {})
            st.metric("VAN optimal", f"{indicateurs2.get('VAN', 'N/A'):,} €" if isinstance(indicateurs2.get('VAN'), (int, float)) else "N/A")
            st.metric("TRI optimal", f"{indicateurs2.get('TRI', 'N/A')} %" if isinstance(indicateurs2.get('TRI'), (int, float)) else "N/A")
    
    def _show_monte_carlo_comparison(self, comparison_data):
        """Affiche la comparaison Monte Carlo"""
        st.subheader("🎲 Comparaison Monte Carlo")
        
        monte_carlo1 = comparison_data['monte_carlo1']
        monte_carlo2 = comparison_data['monte_carlo2']
        
        if not monte_carlo1 and not monte_carlo2:
            st.warning("Aucun résultat Monte Carlo disponible pour la comparaison")
            return
        
        # Afficher les statistiques de risque
        self._show_risk_statistics(monte_carlo1, monte_carlo2, comparison_data)
        
        # Graphique des distributions VAN
        self._plot_van_distributions(monte_carlo1, monte_carlo2, comparison_data)
    
    def _plot_van_distributions(self, mc1, mc2, comparison_data):
        """Trace les distributions de VAN Monte Carlo"""
        try:
            if not mc1 or not mc2:
                return
            
            # Prendre le premier scénario de chaque projet
            scenario1 = list(mc1.keys())[0]
            scenario2 = list(mc2.keys())[0]
            
            data1 = mc1[scenario1]
            data2 = mc2[scenario2]
            
            # Créer l'histogramme des distributions
            fig = go.Figure()
            
            if 'van_distribution' in data1:
                fig.add_trace(go.Histogram(
                    x=data1['van_distribution'],
                    name=comparison_data['manifest1']['name'],
                    opacity=0.7,
                    nbinsx=50
                ))
            
            if 'van_distribution' in data2:
                fig.add_trace(go.Histogram(
                    x=data2['van_distribution'],
                    name=comparison_data['manifest2']['name'],
                    opacity=0.7,
                    nbinsx=50
                ))
            
            fig.update_layout(
                title="Distribution des VAN - Analyse Monte Carlo",
                xaxis_title="VAN (€)",
                yaxis_title="Fréquence",
                barmode='overlay',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des distributions Monte Carlo: {e}")
            st.error("Erreur lors de la génération des distributions Monte Carlo")
    
    def _show_risk_statistics(self, mc1, mc2, comparison_data):
        """Affiche les statistiques de risque"""
        if not mc1 or not mc2:
            return
        
        # Prendre le premier scénario de chaque projet
        scenario1 = list(mc1.keys())[0]
        scenario2 = list(mc2.keys())[0]
        
        data1 = mc1[scenario1]
        data2 = mc2[scenario2]
        
        stats1 = data1.get('statistics', {})
        stats2 = data2.get('statistics', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {comparison_data['manifest1']['name']}")
            for key, value in stats1.items():
                formatted_value = self._format_stat_value(value, key)
                st.metric(key.replace('_', ' ').title(), formatted_value)
        
        with col2:
            st.markdown(f"### {comparison_data['manifest2']['name']}")
            for key, value in stats2.items():
                formatted_value = self._format_stat_value(value, key)
                st.metric(key.replace('_', ' ').title(), formatted_value)
    
    def _format_stat_value(self, value, key):
        """Formate une valeur statistique pour l'affichage"""
        if isinstance(value, (int, float)):
            if 'van' in key.lower() or 'mean' in key.lower():
                return f"{value:,.0f} €"
            elif 'std' in key.lower() or 'ecart' in key.lower():
                return f"{value:,.0f}"
            elif 'percentile' in key.lower() or 'quantile' in key.lower():
                return f"{value:,.0f} €"
            else:
                return f"{value:.2f}"
        return str(value)