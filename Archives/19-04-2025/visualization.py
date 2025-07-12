import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import io

class VisualizationModule:
    def __init__(self):
        # Initialiser les structures de données si elles n'existent pas
        if 'custom_charts' not in st.session_state:
            st.session_state.custom_charts = {}
        
        if 'dashboard_config' not in st.session_state:
            self.initialize_default_dashboard()
    
    def initialize_default_dashboard(self):
        """Initialise la configuration par défaut du dashboard"""
        st.session_state.dashboard_config = {
            'production_consumption': True,
            'autoconsumption_rate': True,
            'monthly_averages': True,
            'daily_pattern': True,
            'financial_indicators': True,
            'optimization_results': True,
            'monte_carlo_results': True
        }
    
    def create_production_consumption_chart(self, date_range=None):
        """
        Crée un graphique de production et consommation
        
        Args:
            date_range: Tuple de (date_début, date_fin) pour filtrer les données
            
        Returns:
            Figure: Objet figure plotly
        """
        if st.session_state.processed_data is None:
            return None
        
        # Copier les données pour ne pas les modifier
        data = st.session_state.processed_data.copy()
        
        # Utiliser des noms standardisés pour les colonnes
        date_col = 'Temps'
        prod_col = 'production_kwh'
        cons_col = 'consumption_kwh'
        
        # Vérifier que les colonnes existent
        missing_cols = []
        for col in [date_col, prod_col, cons_col]:
            if col not in data.columns:
                missing_cols.append(col)
        
        if missing_cols:
            st.error(f"Colonnes manquantes dans les données : {', '.join(missing_cols)}")
            return None
        
        # Calculer l'autoconsommation (si pas déjà fait)
        if 'autoconsumption_kwh' not in data.columns:
            data['autoconsumption_kwh'] = data.apply(
                lambda row: min(row[prod_col], row[cons_col]), 
                axis=1
            )
        
        # Calculer le surplus (si pas déjà fait)
        if 'surplus_kwh' not in data.columns:
            data['surplus_kwh'] = data.apply(
                lambda row: max(0, row[prod_col] - row[cons_col]), 
                axis=1
            )
        
        # Filtrer par plage de dates si spécifiée
        if date_range is not None and isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            data = data[
                (data[date_col] >= pd.Timestamp(start_date)) &
                (data[date_col] <= pd.Timestamp(end_date))
            ]
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data[date_col],
            y=data[prod_col],
            name='Production',
            line=dict(color='gold', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 215, 0, 0.1)'
        ))
        
        fig.add_trace(go.Scatter(
            x=data[date_col],
            y=data[cons_col],
            name='Consommation',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 0, 255, 0.1)'
        ))
        
        fig.add_trace(go.Scatter(
            x=data[date_col],
            y=data['autoconsumption_kwh'],
            name='Autoconsommation',
            line=dict(color='green', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 128, 0, 0.1)'
        ))
        
        fig.add_trace(go.Scatter(
            x=data[date_col],
            y=data['surplus_kwh'],
            name='Surplus',
            line=dict(color='orange', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 165, 0, 0.1)'
        ))
        
        fig.update_layout(
            title="Production, Consommation et Autoconsommation",
            xaxis_title="Date",
            yaxis_title="Énergie (kWh)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified"
        )
        
        return fig
    
    def create_autoconsumption_rate_chart(self, date_range=None):
        """
        Crée un graphique du taux d'autoconsommation
        
        Args:
            date_range: Tuple de (date_début, date_fin) pour filtrer les données
            
        Returns:
            Figure: Objet figure plotly
        """
        if st.session_state.processed_data is None:
            return None
        
        # Copier les données pour ne pas les modifier
        data = st.session_state.processed_data.copy()
        
        # Utiliser des noms standardisés pour les colonnes
        date_col = 'Temps'
        prod_col = 'production_kwh'
        cons_col = 'consumption_kwh'
        
        # Filtrer par plage de dates si spécifiée
        if date_range is not None and isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            data = data[
                (data[date_col] >= pd.Timestamp(start_date)) &
                (data[date_col] <= pd.Timestamp(end_date))
            ]
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data[date_col],
            y=data['autoconsumption_rate'] * 100,
            name="Taux d'autoconsommation",
            line=dict(color='green', width=2),
            fill='tozeroy',
            fillcolor='rgba(0, 128, 0, 0.1)'
        ))
        
        fig.add_trace(go.Scatter(
            x=data[date_col],
            y=data['autoproduction_rate'] * 100,
            name="Taux d'autoproduction",
            line=dict(color='orange', width=2),
            fill='tozeroy',
            fillcolor='rgba(255, 165, 0, 0.1)'
        ))
        
        # Ajouter une ligne horizontale pour la moyenne du taux d'autoconsommation
        avg_autoconsumption_rate = (data['autoconsumption_kwh'].sum() / data[prod_col].sum()) * 100 if data[prod_col].sum() > 0 else 0
        
        fig.add_shape(
            type="line",
            x0=data[date_col].min(),
            y0=avg_autoconsumption_rate,
            x1=data[date_col].max(),
            y1=avg_autoconsumption_rate,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        fig.add_annotation(
            x=data[date_col].max(),
            y=avg_autoconsumption_rate,
            text=f"Moyenne: {avg_autoconsumption_rate:.2f}%",
            showarrow=False,
            yshift=10,
            font=dict(
                color="red"
            )
        )
        
        fig.update_layout(
            title="Taux d'Autoconsommation et d'Autoproduction",
            xaxis_title="Date",
            yaxis_title="Taux (%)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified",
            yaxis=dict(range=[0, 100])
        )
        
        return fig
    
    def create_monthly_averages_chart(self):
        """
        Crée un graphique des moyennes mensuelles
        
        Returns:
            Figure: Objet figure plotly
        """
        if st.session_state.processed_data is None:
            return None
        
        # Copier les données pour ne pas les modifier
        data = st.session_state.processed_data.copy()
        
        # Utiliser des noms standardisés pour les colonnes
        date_col = 'Temps'
        prod_col = 'production_kwh'
        cons_col = 'consumption_kwh'
        
        # Extraire le mois et l'année
        data['month'] = data[date_col].dt.strftime('%Y-%m')
        
        # Calculer les moyennes mensuelles
        monthly_data = data.groupby('month').agg({
            'production_kwh': 'sum',
            'consumption_kwh': 'sum',
            'autoconsumption_kwh': 'sum',
            'surplus_kwh': 'sum'
        }).reset_index()
        
        # Calculer les taux d'autoconsommation mensuels
        monthly_data['autoconsumption_rate'] = monthly_data['autoconsumption_kwh'] / monthly_data['production_kwh']
        monthly_data['autoproduction_rate'] = monthly_data['autoconsumption_kwh'] / monthly_data['consumption_kwh']
        
        # Créer le graphique
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Énergie Mensuelle (kWh)", "Taux Mensuels (%)")
        )
        
        # Premier sous-graphique: Énergie
        fig.add_trace(
            go.Bar(
                x=monthly_data['month'],
                y=monthly_data['production_kwh'],
                name='Production',
                marker_color='gold'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=monthly_data['month'],
                y=monthly_data['consumption_kwh'],
                name='Consommation',
                marker_color='blue'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=monthly_data['month'],
                y=monthly_data['autoconsumption_kwh'],
                name='Autoconsommation',
                marker_color='green'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=monthly_data['month'],
                y=monthly_data['surplus_kwh'],
                name='Surplus',
                marker_color='orange'
            ),
            row=1, col=1
        )
        
        # Deuxième sous-graphique: Taux
        fig.add_trace(
            go.Scatter(
                x=monthly_data['month'],
                y=monthly_data['autoconsumption_rate'] * 100,
                name="Taux d'autoconsommation",
                mode='lines+markers',
                line=dict(color='green', width=2),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=monthly_data['month'],
                y=monthly_data['autoproduction_rate'] * 100,
                name="Taux d'autoproduction",
                mode='lines+markers',
                line=dict(color='orange', width=2),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
        
        # Mise en page
        fig.update_layout(
            title="Analyse Mensuelle de la Production et Consommation",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=700,
            barmode='group'
        )
        
        fig.update_yaxes(title_text="Énergie (kWh)", row=1, col=1)
        fig.update_yaxes(title_text="Taux (%)", range=[0, 100], row=2, col=1)
        fig.update_xaxes(title_text="Mois", row=2, col=1)
        
        return fig
    
    def create_daily_pattern_chart(self):
        """
        Crée un graphique des profils journaliers (si les données sont disponibles à cette granularité)
        
        Returns:
            Figure: Objet figure plotly ou None si les données ne sont pas disponibles
        """
        if st.session_state.processed_data is None:
            return None
        
        # Copier les données pour ne pas les modifier
        data = st.session_state.processed_data.copy()
        
        # Utiliser des noms standardisés pour les colonnes
        date_col = 'Temps'
        
        # Vérifier si les données ont une granularité horaire ou inférieure
        # Si non, retourner None
        time_diff = data[date_col].diff().min()
        if time_diff is pd.NaT or time_diff > timedelta(hours=1):
            return None
        
        # Extraire l'heure
        data['hour'] = data[date_col].dt.hour
        
        # Calculer les moyennes horaires
        hourly_data = data.groupby('hour').agg({
            'production_kwh': 'mean',
            'consumption_kwh': 'mean',
            'autoconsumption_kwh': 'mean',
            'surplus_kwh': 'mean'
        }).reset_index()
        
        # Créer le graphique
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hourly_data['hour'],
            y=hourly_data['production_kwh'],
            name='Production',
            mode='lines+markers',
            line=dict(color='gold', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=hourly_data['hour'],
            y=hourly_data['consumption_kwh'],
            name='Consommation',
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=hourly_data['hour'],
            y=hourly_data['autoconsumption_kwh'],
            name='Autoconsommation',
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=hourly_data['hour'],
            y=hourly_data['surplus_kwh'],
            name='Surplus',
            mode='lines+markers',
            line=dict(color='orange', width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Profil Journalier Moyen",
            xaxis_title="Heure",
            yaxis_title="Énergie Moyenne (kWh)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(0, 24)),
                ticktext=[f"{h}h" for h in range(0, 24)]
            )
        )
        
        return fig
    
    def create_financial_indicators_chart(self, scenario=None):
        """
        Crée un graphique des indicateurs financiers
        
        Args:
            scenario: Nom du scénario à afficher (si None, utilise le premier disponible)
            
        Returns:
            Figure: Objet figure plotly ou None si aucun résultat n'est disponible
        """
        if not hasattr(st.session_state, 'economic_results') or not st.session_state.economic_results:
            return None
        
        # Si aucun scénario n'est spécifié, utiliser le premier disponible
        if scenario is None:
            scenario = list(st.session_state.economic_results.keys())[0]
        
        # Vérifier que le scénario existe
        if scenario not in st.session_state.economic_results:
            return None
        
        # Récupérer les résultats
        results = st.session_state.economic_results[scenario]
        
        # Créer un DataFrame pour le graphique
        df_financial = pd.DataFrame({
            "Année": results['years'],
            "Revenus": results['revenues'],
            "OPEX": results['opex'],
            "EBITDA": results['ebitda'],
            "Service de la Dette": results['debt_service'],
            "Free Cash Flow": results['free_cash_flow'],
            "Flux Cumulé": results['cumulative_cash_flow'],
            "DSCR": results['dscr']
        })
        
        # Créer le graphique
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f"Flux Financiers - Scénario {scenario}", "DSCR")
        )
        
        # Premier sous-graphique: Flux financiers
        fig.add_trace(
            go.Bar(
                x=df_financial['Année'],
                y=df_financial['Revenus'],
                name='Revenus',
                marker_color='green'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=df_financial['Année'],
                y=df_financial['OPEX'],
                name='OPEX',
                marker_color='red'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df_financial['Année'],
                y=df_financial['Free Cash Flow'],
                name='Free Cash Flow',
                mode='lines+markers',
                line=dict(color='purple', width=2),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df_financial['Année'],
                y=df_financial['Flux Cumulé'],
                name='Flux Cumulé',
                mode='lines+markers',
                line=dict(color='orange', width=2),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Deuxième sous-graphique: DSCR
        fig.add_trace(
            go.Scatter(
                x=df_financial['Année'],
                y=df_financial['DSCR'],
                name='DSCR',
                mode='lines+markers',
                line=dict(color='blue', width=2),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
        
        # Ajouter une ligne horizontale pour le DSCR cible
        target_dscr = st.session_state.config.get('target_dscr', 1.2)
        fig.add_shape(
            type="line",
            x0=df_financial['Année'].min(),
            y0=target_dscr,
            x1=df_financial['Année'].max(),
            y1=target_dscr,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=2, col=1
        )
        
        # Mise en page
        fig.update_layout(
            height=700,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(title_text="Montant (€)", row=1, col=1)
        fig.update_yaxes(title_text="DSCR", row=2, col=1)
        fig.update_xaxes(title_text="Année", row=2, col=1)
        
        return fig
    
    def create_optimization_results_chart(self, scenario=None):
        """
        Crée un graphique des résultats d'optimisation
        
        Args:
            scenario: Nom du scénario à afficher (si None, utilise le premier disponible)
            
        Returns:
            Figure: Objet figure plotly ou None si aucun résultat n'est disponible
        """
        if not hasattr(st.session_state, 'optimization_results') or not st.session_state.optimization_results:
            return None
        
        # Si aucun scénario n'est spécifié, utiliser le premier disponible
        if scenario is None:
            scenario = list(st.session_state.optimization_results.keys())[0]
        
        # Vérifier que le scénario existe
        if scenario not in st.session_state.optimization_results:
            return None
        
        # Récupérer les résultats
        results = st.session_state.optimization_results[scenario]
        
        # Créer un DataFrame avec les résultats pour chaque prix
        data = []
        for prix, res in results['tous_resultats'].items():
            if res is not None:
                data.append({
                    "Prix (€/kWh)": prix,
                    "ROI (%)": res['roi'] * 100,
                    "TRI (%)": res['irr'] * 100 if res['irr'] is not None else 0,
                    "VAN (€)": res['npv'],
                    "Période de Récupération (ans)": res['payback_period'] if res['payback_period'] != float('inf') else 30,
                    "DSCR moyen": res['avg_dscr'] if res['avg_dscr'] != float('inf') else 5
                })
        
        df_results = pd.DataFrame(data)
        
        # Extraire le prix optimal
        prix_optimal = results['prix_optimal']
        
        # Créer le graphique
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f"ROI et TRI - Scénario {scenario}", "VAN et Période de Récupération")
        )
        
        # Premier sous-graphique: ROI et TRI
        fig.add_trace(
            go.Scatter(
                x=df_results["Prix (€/kWh)"],
                y=df_results["ROI (%)"],
                name='ROI (%)',
                mode='lines+markers',
                line=dict(color='blue', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df_results["Prix (€/kWh)"],
                y=df_results["TRI (%)"],
                name='TRI (%)',
                mode='lines+markers',
                line=dict(color='green', width=2),
                marker=dict(size=6)
            ),
            row=1, col=1
        )
        
        # Deuxième sous-graphique: VAN et Période de Récupération
        fig.add_trace(
            go.Scatter(
                x=df_results["Prix (€/kWh)"],
                y=df_results["VAN (€)"],
                name='VAN (€)',
                mode='lines+markers',
                line=dict(color='purple', width=2),
                marker=dict(size=6),
                yaxis="y3"
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df_results["Prix (€/kWh)"],
                y=df_results["Période de Récupération (ans)"],
                name='Période de Récupération (ans)',
                mode='lines+markers',
                line=dict(color='orange', width=2),
                marker=dict(size=6),
                yaxis="y4"
            ),
            row=2, col=1
        )
        
        # Ajouter une ligne verticale pour le prix optimal sur les deux sous-graphiques
        fig.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results[["ROI (%)", "TRI (%)"]].max().max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=1, col=1
        )
        
        fig.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results["VAN (€)"].max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=2, col=1
        )
        
        # Ajouter une annotation pour le prix optimal
        fig.add_annotation(
            x=prix_optimal,
            y=df_results[["ROI (%)", "TRI (%)"]].max().max() * 1.05,
            text=f"Prix optimal: {prix_optimal:.4f} €/kWh",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red",
            font=dict(
                size=12,
                color="red"
            ),
            align="center",
            row=1, col=1
        )
        
        # Mise en page
        fig.update_layout(
            height=700,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(title_text="Pourcentage (%)", row=1, col=1)
        fig.update_yaxes(title_text="VAN (€)", row=2, col=1)
        fig.update_yaxes(title_text="Période (ans)", overlaying="y", side="right", row=2, col=1)
        fig.update_xaxes(title_text="Prix de Revente (€/kWh)", row=2, col=1)
        
        return fig
    
    def create_monte_carlo_results_chart(self, scenario=None):
        """
        Crée un graphique des résultats de la simulation Monte Carlo
        
        Args:
            scenario: Nom du scénario à afficher (si None, utilise le premier disponible)
            
        Returns:
            Figure: Objet figure plotly ou None si aucun résultat n'est disponible
        """
        if not hasattr(st.session_state, 'monte_carlo_results') or not st.session_state.monte_carlo_results:
            return None
        
        # Si aucun scénario n'est spécifié, utiliser le premier disponible
        if scenario is None:
            scenario = list(st.session_state.monte_carlo_results.keys())[0]
        
        # Vérifier que le scénario existe
        if scenario not in st.session_state.monte_carlo_results:
            return None
        
        # Récupérer les résultats
        results = st.session_state.monte_carlo_results[scenario]
        
        # Créer le graphique
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Distribution du ROI", "Distribution du TRI", "Distribution de la VAN", "Distribution du DSCR"),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # Sous-graphique 1: ROI
        fig.add_trace(
            go.Histogram(
                x=[r*100 for r in results['roi_values']],  # Convertir en pourcentage
                name='ROI (%)',
                marker_color='blue',
                opacity=0.7,
                nbinsx=30
            ),
            row=1, col=1
        )
        
        # Ligne verticale pour la moyenne du ROI
        roi_mean = results['statistics']['roi']['mean'] * 100
        fig.add_shape(
            type="line",
            x0=roi_mean,
            y0=0,
            x1=roi_mean,
            y1=50,  # Approximation de la hauteur
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=1, col=1
        )
        
        # Ligne verticale pour le seuil minimal du ROI
        fig.add_shape(
            type="line",
            x0=5,  # 5%
            y0=0,
            x1=5,
            y1=50,
            line=dict(
                color="green",
                width=2,
                dash="dash",
            ),
            row=1, col=1
        )
        
        # Sous-graphique 2: TRI
        fig.add_trace(
            go.Histogram(
                x=[r*100 for r in results['irr_values']],  # Convertir en pourcentage
                name='TRI (%)',
                marker_color='green',
                opacity=0.7,
                nbinsx=30
            ),
            row=1, col=2
        )
        
        # Ligne verticale pour la moyenne du TRI
        irr_mean = results['statistics']['irr']['mean'] * 100
        fig.add_shape(
            type="line",
            x0=irr_mean,
            y0=0,
            x1=irr_mean,
            y1=50,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=1, col=2
        )
        
        # Ligne verticale pour le seuil minimal du TRI
        fig.add_shape(
            type="line",
            x0=4,  # 4%
            y0=0,
            x1=4,
            y1=50,
            line=dict(
                color="green",
                width=2,
                dash="dash",
            ),
            row=1, col=2
        )
        
        # Sous-graphique 3: VAN
        fig.add_trace(
            go.Histogram(
                x=results['npv_values'],
                name='VAN (€)',
                marker_color='purple',
                opacity=0.7,
                nbinsx=30
            ),
            row=2, col=1
        )
        
        # Ligne verticale pour la moyenne de la VAN
        npv_mean = results['statistics']['npv']['mean']
        fig.add_shape(
            type="line",
            x0=npv_mean,
            y0=0,
            x1=npv_mean,
            y1=50,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=2, col=1
        )
        
        # Ligne verticale pour le seuil minimal de la VAN (0)
        fig.add_shape(
            type="line",
            x0=0,
            y0=0,
            x1=0,
            y1=50,
            line=dict(
                color="green",
                width=2,
                dash="dash",
            ),
            row=2, col=1
        )
        
        # Sous-graphique 4: DSCR
        fig.add_trace(
            go.Histogram(
                x=results['dscr_values'],
                name='DSCR',
                marker_color='red',
                opacity=0.7,
                nbinsx=30
            ),
            row=2, col=2
        )
        
        # Ligne verticale pour la moyenne du DSCR
        dscr_mean = results['statistics']['dscr']['mean']
        fig.add_shape(
            type="line",
            x0=dscr_mean,
            y0=0,
            x1=dscr_mean,
            y1=50,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            row=2, col=2
        )
        
        # Ligne verticale pour le seuil minimal du DSCR
        target_dscr = st.session_state.config.get('target_dscr', 1.2)
        fig.add_shape(
            type="line",
            x0=target_dscr,
            y0=0,
            x1=target_dscr,
            y1=50,
            line=dict(
                color="green",
                width=2,
                dash="dash",
            ),
            row=2, col=2
        )
        
        # Mise en page
        fig.update_layout(
            title=f"Résultats de la Simulation Monte Carlo - Scénario {scenario}",
            height=800,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="ROI (%)", row=1, col=1)
        fig.update_xaxes(title_text="TRI (%)", row=1, col=2)
        fig.update_xaxes(title_text="VAN (€)", row=2, col=1)
        fig.update_xaxes(title_text="DSCR", row=2, col=2)
        
        fig.update_yaxes(title_text="Fréquence", row=1, col=1)
        fig.update_yaxes(title_text="Fréquence", row=1, col=2)
        fig.update_yaxes(title_text="Fréquence", row=2, col=1)
        fig.update_yaxes(title_text="Fréquence", row=2, col=2)
        
        return fig
    
    def create_custom_chart(self, chart_type, x_data, y_data, title, x_label, y_label):
        """
        Crée un graphique personnalisé
        
        Args:
            chart_type: Type de graphique ('line', 'bar', 'scatter', 'pie', 'histogram')
            x_data: Données pour l'axe X
            y_data: Données pour l'axe Y
            title: Titre du graphique
            x_label: Libellé de l'axe X
            y_label: Libellé de l'axe Y
            
        Returns:
            Figure: Objet figure plotly
        """
        fig = None
        
        if chart_type == 'line':
            fig = px.line(x=x_data, y=y_data, title=title, labels={'x': x_label, 'y': y_label})
        elif chart_type == 'bar':
            fig = px.bar(x=x_data, y=y_data, title=title, labels={'x': x_label, 'y': y_label})
        elif chart_type == 'scatter':
            fig = px.scatter(x=x_data, y=y_data, title=title, labels={'x': x_label, 'y': y_label})
        elif chart_type == 'pie':
            fig = px.pie(values=y_data, names=x_data, title=title)
        elif chart_type == 'histogram':
            fig = px.histogram(x=y_data, title=title, labels={'x': y_label, 'y': 'Fréquence'})
        
        return fig
    
    def export_chart_as_image(self, fig, filename):
        """
        Exporte un graphique au format image
        
        Args:
            fig: Objet figure plotly
            filename: Nom du fichier de sortie
            
        Returns:
            bool: True si l'export a réussi, False sinon
        """
        try:
            fig.write_image(filename)
            return True
        except:
            return False
    
    def show_ui(self):
        """
        Affiche l'interface utilisateur pour la visualisation et le dashboard
        """
        st.title("Analyse Financière Avancée")
        
        # Vérifier si des scénarios et résultats économiques sont disponibles
        if not hasattr(st.session_state, 'scenarios') or not hasattr(st.session_state, 'economic_results'):
            st.warning("""
            Pour accéder aux graphiques avancés, vous devez d'abord :
            1. Aller dans l'onglet 'Analyse Économique'
            2. Configurer vos paramètres économiques (CAPEX, OPEX, prix de revente, etc.)
            3. Créer un ou plusieurs scénarios
            4. Lancer l'analyse économique pour chaque scénario
            """)
            return
        
        # Sélecteur de type de graphique avancé
        advanced_chart_type = st.selectbox(
            "Type de graphique",
            options=[
                "Cascade du Cash-flow",
                "Analyse Tornado",
                "Heatmap TRI vs CAPEX-OPEX"
            ],
            index=0
        )
        
        # Sélecteur de scénario
        available_scenarios = [s for s in st.session_state.scenarios.keys() 
                             if s in st.session_state.economic_results]
        if not available_scenarios:
            st.warning("""
            Aucun scénario avec résultats économiques disponibles.
            Veuillez d'abord effectuer une analyse économique dans l'onglet 'Analyse Économique'.
            """)
            return
            
        selected_scenario = st.selectbox(
            "Sélectionner un scénario",
            options=available_scenarios,
            index=0
        )
        
        # Afficher le graphique sélectionné
        if advanced_chart_type == "Cascade du Cash-flow":
            # Sélecteur d'année pour la cascade de cash-flow
            years = list(range(1, len(st.session_state.economic_results[selected_scenario]['years']) + 1))
            selected_year = st.slider(
                "Sélectionner l'année",
                min_value=1,
                max_value=len(years),
                value=5
            )
            
            # Afficher le graphique
            fig = self.create_waterfall_cashflow_chart(
                st.session_state.economic_results[selected_scenario],
                year_index=selected_year-1
            )
            st.plotly_chart(fig, use_container_width=True)
            
        elif advanced_chart_type == "Analyse Tornado":
            if st.button("Lancer l'analyse de sensibilité"):
                with st.spinner("Calcul en cours..."):
                    # Paramètres à analyser
                    parameters = {
                        'capex': 'CAPEX',
                        'opex': 'OPEX',
                        'sell_price': 'Prix de revente',
                        'buy_price': "Prix d'achat",
                        'inflation': 'Taux d\'inflation',
                        'discount_rate': 'Taux d\'actualisation'
                    }
                    
                    # Calculer les résultats de sensibilité
                    sensitivity_results = {}
                    for param, label in parameters.items():
                        sensitivity_results[param] = self.calculate_sensitivity(
                            selected_scenario,
                            param,
                            st.session_state.economic_analysis_module
                        )
                    
                    # Créer et afficher le graphique tornado
                    fig = self.create_tornado_chart(
                        sensitivity_results,
                        list(parameters.values()),
                        st.session_state.scenarios[selected_scenario]
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
        elif advanced_chart_type == "Heatmap TRI vs CAPEX-OPEX":
            if st.button("Générer la heatmap"):
                with st.spinner("Calcul en cours..."):
                    fig = self.create_heatmap_irr_capex_opex(
                        selected_scenario,
                        st.session_state.economic_analysis_module
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    def create_waterfall_cashflow_chart(self, results, year_index=5):
        """
        Crée un graphique en cascade du cash-flow pour une année spécifique
        
        Args:
            results: Dictionnaire contenant les résultats financiers
            year_index: Index de l'année à analyser (par défaut: 5ème année)
            
        Returns:
            Figure: Objet figure plotly
        """
        # Assurer que l'année demandée est disponible
        if year_index >= len(results['years']):
            year_index = len(results['years']) - 1
        
        # Année sélectionnée
        year = results['years'][year_index]
        
        # Extraire les composantes du cash-flow pour cette année
        components = []
        values = []
        
        # Si c'est la première année, inclure le CAPEX initial
        if year_index == 0:
            components.append("CAPEX initial")
            values.append(-results['capex'])
        
        # Revenus d'autoconsommation (calculé à partir des données disponibles)
        autoconsumption_revenue = results['annual_autoconsumption'][year_index] * results['prix_revente']
        components.append("Revenus autoconsommation")
        values.append(autoconsumption_revenue)
        
        # Revenus de surplus
        surplus_revenue = results['annual_surplus'][year_index] * results['prix_revente']
        components.append("Revenus surplus")
        values.append(surplus_revenue)
        
        # OPEX (négatif)
        components.append("OPEX")
        values.append(-results['opex'][year_index])
        
        # Intérêts payés (négatif)
        if 'interest_paid' in results:
            components.append("Intérêts")
            values.append(-results['interest_paid'][year_index])
        
        # Taxes (négatif)
        if 'taxes' in results:
            components.append("Taxes")
            values.append(-results['taxes'][year_index])
        
        # Remboursement du principal (négatif)
        if 'principal_paid' in results:
            components.append("Remboursement principal")
            values.append(-results['principal_paid'][year_index])
        
        # Cash-flow net
        components.append("Cash-flow net")
        # Le dernier élément sera calculé automatiquement par Plotly
        
        # Créer le graphique en cascade
        fig = go.Figure(go.Waterfall(
            name="Analyse du cash-flow",
            orientation="v",
            measure=["relative"] * (len(components) - 1) + ["total"],
            x=components,
            textposition="outside",
            text=[f"{abs(val):,.0f}€" for val in values] + [""],
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#FF4136"}},  # Rouge pour les valeurs négatives
            increasing={"marker": {"color": "#3D9970"}},  # Vert pour les valeurs positives
            totals={"marker": {"color": "#1E88E5"}}      # Bleu pour le total
        ))
        
        fig.update_layout(
            title=f"Cascade du Cash-flow - Année {year}",
            showlegend=False,
            height=600,
            xaxis_title="Composantes",
            yaxis_title="Montant (€)",
            yaxis=dict(
                tickformat=",d €"
            )
        )
        
        return fig
    
    def create_tornado_chart(self, sensitivity_results, parameter_names, base_value, target_metric='npv'):
        """
        Crée un graphique Tornado montrant l'impact des variations de paramètres sur une métrique cible
        
        Args:
            sensitivity_results: Dictionnaire contenant les résultats des analyses de sensibilité
                Format: {parameter_name: {parameter_value: results_dict}}
            parameter_names: Liste des noms des paramètres (pour l'ordre d'affichage)
            base_value: Valeur de la métrique pour le cas de base
            target_metric: Métrique cible ('npv', 'irr', 'roi', etc.)
            
        Returns:
            Figure: Objet figure plotly
        """
        # Préparer les données
        parameters = []
        lower_values = []
        upper_values = []
        
        for param in parameter_names:
            if param not in sensitivity_results:
                continue
                
            # Extraire les valeurs testées et les résultats
            param_values = sorted(sensitivity_results[param].keys())
            metric_values = []
            
            for val in param_values:
                if target_metric == 'irr':
                    # Convertir en pourcentage pour le TRI
                    metric_value = sensitivity_results[param][val][target_metric] * 100 if sensitivity_results[param][val][target_metric] is not None else 0
                elif target_metric in ['npv', 'roi', 'payback_period', 'avg_dscr']:
                    metric_value = sensitivity_results[param][val][target_metric]
                else:
                    # Valeur par défaut
                    metric_value = 0
                    
                metric_values.append(metric_value)
            
            # Si nous avons au moins 2 valeurs, utiliser min et max pour le tornado
            if len(metric_values) >= 2:
                parameters.append(param)
                lower_values.append(min(metric_values) - base_value)
                upper_values.append(max(metric_values) - base_value)
        
        # Trier par impact (différence entre max et min)
        impact = [abs(upper - lower) for upper, lower in zip(upper_values, lower_values)]
        sorted_indices = sorted(range(len(impact)), key=lambda i: impact[i], reverse=True)
        
        parameters = [parameters[i] for i in sorted_indices]
        lower_values = [lower_values[i] for i in sorted_indices]
        upper_values = [upper_values[i] for i in sorted_indices]
        
        # Créer les étiquettes pour les paramètres
        param_labels = {
            'prix_revente': 'Prix de revente (€/kWh)',
            'inflation': 'Taux d\'inflation (%)',
            'opex': 'OPEX (€/an)',
            'capex': 'CAPEX (€)',
            'debt_ratio': 'Ratio Dette/Total',
            'debt_term_years': 'Durée du prêt (années)',
            'degradation_rate': 'Taux de dégradation (%)'
        }
        
        # Utiliser les étiquettes formatées ou les noms bruts si non disponibles
        formatted_params = [param_labels.get(p, p) for p in parameters]
        
        # Créer le graphique tornado
        fig = go.Figure()
        
        # Barre pour les valeurs inférieures (généralement effet négatif)
        fig.add_trace(go.Bar(
            y=formatted_params,
            x=lower_values,
            name='Impact négatif',
            orientation='h',
            marker=dict(color='#FF4136'),
            showlegend=True
        ))
        
        # Barre pour les valeurs supérieures (généralement effet positif)
        fig.add_trace(go.Bar(
            y=formatted_params,
            x=upper_values,
            name='Impact positif',
            orientation='h',
            marker=dict(color='#3D9970'),
            showlegend=True
        ))
        
        # Ligne verticale pour la valeur de base
        fig.add_shape(
            type="line",
            x0=0, y0=-0.5,
            x1=0, y1=len(parameters) - 0.5,
            line=dict(color="black", width=2, dash="dash")
        )
        
        # Formater le titre en fonction de la métrique cible
        metric_labels = {
            'npv': 'VAN (€)',
            'irr': 'TRI (%)',
            'roi': 'ROI (%)',
            'payback_period': 'Période de Récupération (ans)',
            'avg_dscr': 'DSCR moyen'
        }
        
        metric_label = metric_labels.get(target_metric, target_metric)
        
        fig.update_layout(
            title=f"Analyse Tornado: Impact des paramètres sur {metric_label}",
            barmode='relative',
            height=600,
            xaxis_title=f"Variation de {metric_label} par rapport au cas de base",
            yaxis=dict(
                title="Paramètres",
                autorange="reversed"  # Pour avoir l'impact le plus fort en haut
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_heatmap_irr_capex_opex(self, scenario_name, economic_analysis_module):
        """
        Crée une heatmap montrant le TRI en fonction des variations de CAPEX et OPEX
        
        Args:
            scenario_name: Nom du scénario à analyser
            economic_analysis_module: Instance du module d'analyse économique
            
        Returns:
            Figure: Objet figure plotly
        """
        # Vérifier que le scénario existe
        if scenario_name not in st.session_state.scenarios:
            st.error(f"Scénario '{scenario_name}' non trouvé")
            return None
        
        # Récupérer le scénario de base
        base_scenario = st.session_state.scenarios[scenario_name]
        
        # Définir les variations de CAPEX et OPEX
        capex_variations = np.linspace(0.5, 1.5, 11)  # De -50% à +50%
        opex_variations = np.linspace(0.5, 1.5, 11)   # De -50% à +50%
        
        # Initialiser la matrice des TRI
        irr_matrix = np.zeros((len(capex_variations), len(opex_variations)))
        
        # Calculer les TRI pour chaque combinaison
        for i, capex_factor in enumerate(capex_variations):
            for j, opex_factor in enumerate(opex_variations):
                # Créer une copie du scénario avec les variations
                modified_scenario = base_scenario.copy()
                modified_scenario['capex'] *= capex_factor
                modified_scenario['opex'] *= opex_factor
                
                # Calculer les indicateurs financiers
                results = economic_analysis_module.calculate_financial_indicators(modified_scenario)
                irr_matrix[i, j] = results['irr']
        
        # Créer la heatmap
        fig = go.Figure(data=go.Heatmap(
            z=irr_matrix,
            x=opex_variations,
            y=capex_variations,
            colorscale='RdYlGn',
            colorbar=dict(
                title='TRI (%)',
                titleside='right'
            ),
            hovertemplate='CAPEX: %{y:.1f}x<br>OPEX: %{x:.1f}x<br>TRI: %{z:.1f}%<extra></extra>'
        ))
        
        # Mettre à jour le layout
        fig.update_layout(
            title=f"Heatmap TRI vs CAPEX-OPEX - Scénario {scenario_name}",
            xaxis_title="Facteur OPEX",
            yaxis_title="Facteur CAPEX",
            xaxis=dict(
                tickmode='array',
                tickvals=opex_variations,
                ticktext=[f'{x:.1f}x' for x in opex_variations]
            ),
            yaxis=dict(
                tickmode='array',
                tickvals=capex_variations,
                ticktext=[f'{y:.1f}x' for y in capex_variations]
            ),
            height=600,
            width=800
        )
        
        return fig
    
    def display_key_statistics(self, date_range=None):
        """
        Affiche les statistiques clés de production et consommation
        
        Args:
            date_range: Tuple de (date_début, date_fin) pour filtrer les données
        """
        if st.session_state.processed_data is None:
            st.warning("Aucune donnée disponible.")
            return
        
        # Copier les données pour ne pas les modifier
        data = st.session_state.processed_data.copy()
        
        # Utiliser des noms standardisés pour les colonnes
        date_col = 'Temps'
        prod_col = 'production_kwh'
        cons_col = 'consumption_kwh'
        
        # Filtrer par plage de dates si spécifiée
        if date_range is not None and isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            data = data[
                (data[date_col] >= pd.Timestamp(start_date)) &
                (data[date_col] <= pd.Timestamp(end_date))
            ]
        
        # Calculer les statistiques clés
        production = data[prod_col].sum()
        consumption = data[cons_col].sum()
        
        # Calculer l'autoconsommation élément par élément
        autoconsumption = data.apply(lambda row: min(row[prod_col], row[cons_col]), axis=1).sum()
        
        surplus = production - autoconsumption
        
        # Calculer les taux
        autoconsumption_rate = (autoconsumption / production * 100) if production > 0 else 0
        autoproduction_rate = (autoconsumption / consumption * 100) if consumption > 0 else 0
        
        # Afficher les statistiques
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Production Totale", f"{production:.2f} kWh")
            st.metric("Consommation Totale", f"{consumption:.2f} kWh")
        
        with col2:
            st.metric("Autoconsommation", f"{autoconsumption:.2f} kWh")
            st.metric("Surplus", f"{surplus:.2f} kWh")
        
        with col3:
            st.metric("Taux d'Autoconsommation", f"{autoconsumption_rate:.2f}%")
            st.metric("Taux d'Autoproduction", f"{autoproduction_rate:.2f}%")