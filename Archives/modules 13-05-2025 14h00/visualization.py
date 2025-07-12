import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
            'client_synthesis': True,
            'producer_analysis': True,
            'production_consumption': True,
            'autoconsumption_rate': True,
            'monthly_averages': True,
            'daily_pattern': True,
            'financial_indicators': True,
            'optimization_results': True,
            'monte_carlo_results': True
        }
    
    # ==========================================================================
    # GRAPHIQUES POUR LA SECTION CLIENT
    # ==========================================================================
    
    def create_price_comparison_chart(self, results_data, config):
        """
        Crée un graphique de comparaison entre le prix optimal et le tarif EDF.
        
        Args:
            results_data: Dictionnaire contenant les résultats financiers
            config: Dictionnaire de configuration
            
        Returns:
            Figure: Objet figure plotly
        """
        if not results_data or 'prix_revente' not in results_data:
            return None
        
        # Récupérer les prix
        prix_optimal = results_data.get('prix_revente', 0)
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        
        # Calculer l'économie en pourcentage
        if tarif_edf > 0:
            economie_pct = ((tarif_edf - prix_optimal) / tarif_edf) * 100
        else:
            economie_pct = 0
        
        # Créer le graphique
        fig = go.Figure()
        
        # Ajouter les barres pour les prix
        fig.add_trace(go.Bar(
            x=['Prix Optimal', 'Tarif EDF'],
            y=[prix_optimal, tarif_edf],
            text=[f"{prix_optimal:.4f} €/kWh", f"{tarif_edf:.4f} €/kWh"],
            textposition='outside',
            marker_color=['#2ca02c', '#d62728'],  # Vert pour prix optimal, rouge pour EDF
            hoverinfo='text',
            hovertext=[f"Prix Optimal: {prix_optimal:.4f} €/kWh", f"Tarif EDF: {tarif_edf:.4f} €/kWh"]
        ))
        
        # Ajouter une annotation pour l'économie
        fig.add_annotation(
            x=0.5,
            y=max(prix_optimal, tarif_edf) * 1.15,
            text=f"Économie: {economie_pct:.1f}%",
            showarrow=False,
            font=dict(
                size=14,
                color="#2ca02c" if economie_pct > 0 else "#d62728"
            )
        )
        
        # Mise en page
        fig.update_layout(
            title="Comparaison des Prix (€/kWh)",
            yaxis_title="Prix (€/kWh)",
            showlegend=False,
            height=400,
            yaxis=dict(tickformat=",.4f"),
            xaxis=dict(tickangle=-45)
        )
        
        return fig
    
    def create_annual_savings_chart(self, results_data, config):
        """
        Calcule et affiche l'économie annuelle estimée pour le client.
        
        Args:
            results_data: Dictionnaire contenant les résultats financiers
            config: Dictionnaire de configuration
            
        Returns:
            Figure: Objet figure plotly
        """
        if not results_data or 'monthly_data' not in results_data:
            return None
        
        monthly_data = results_data.get('monthly_data')
        if not isinstance(monthly_data, pd.DataFrame) or monthly_data.empty:
            return None
        
        # Récupérer les prix
        prix_optimal = results_data.get('prix_revente', 0)
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        
        # Calculer l'autoconsommation annuelle
        if 'Autoconsommation_kWh' in monthly_data.columns:
            autoconsommation_annuelle = monthly_data['Autoconsommation_kWh'].sum()
        else:
            return None
        
        # Calculer l'économie
        economie_kwh = tarif_edf - prix_optimal
        economie_annuelle = economie_kwh * autoconsommation_annuelle
        economie_pct = (economie_kwh / tarif_edf) * 100 if tarif_edf > 0 else 0
        
        # Créer un graphique simple avec deux métriques
        fig = go.Figure()
        
        # Ajouter les métriques sous forme de jauge
        fig.add_trace(go.Indicator(
            mode="number+gauge+delta",
            value=economie_annuelle,
            number={"prefix": "", "suffix": " €", "valueformat": ",.2f"},
            title={"text": "Économie Annuelle (€)"},
            gauge={
                "axis": {"range": [0, economie_annuelle * 1.5 if economie_annuelle > 0 else 100]},
                "bar": {"color": "#2ca02c"},
                "steps": [
                    {"range": [0, economie_annuelle], "color": "#e8f5e9"}
                ]
            },
            domain={"row": 0, "column": 0}
        ))
        
        fig.add_trace(go.Indicator(
            mode="number+gauge+delta",
            value=economie_pct,
            number={"suffix": " %", "valueformat": ".1f"},
            title={"text": "Économie (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2ca02c"},
                "steps": [
                    {"range": [0, economie_pct], "color": "#e8f5e9"}
                ]
            },
            domain={"row": 0, "column": 1}
        ))
        
        # Mise en page
        fig.update_layout(
            grid={"rows": 1, "columns": 2, "pattern": "independent"},
            title="Économies pour le Client",
            height=250
        )
        
        return fig
    
    def create_energy_distribution_pie(self, results_data):
        """
        Crée un graphique camembert de la répartition de l'énergie produite.
        
        Args:
            results_data: Dictionnaire contenant les résultats financiers
        
        Returns:
            Figure: Objet figure plotly
        """
        if not results_data or 'monthly_data' not in results_data:
            return None
        
        monthly_data = results_data.get('monthly_data')
        if not isinstance(monthly_data, pd.DataFrame) or monthly_data.empty:
            return None
        
        # Vérifier que les colonnes nécessaires existent
        required_cols = ['Autoconsommation_kWh', 'Surplus_kWh']
        if not all(col in monthly_data.columns for col in required_cols):
            # Tentative de fallback sur d'autres noms de colonnes possibles
            alt_cols = {
                'Autoconsommation_kWh': ['autoconsumption_kwh', 'autoconsommation_kwh'],
                'Surplus_kWh': ['surplus_kwh', 'surplus']
            }
            
            for required, alternatives in alt_cols.items():
                if required not in monthly_data.columns:
                    for alt in alternatives:
                        if alt in monthly_data.columns:
                            monthly_data[required] = monthly_data[alt]
                            break
            
            # Vérifier à nouveau
            if not all(col in monthly_data.columns for col in required_cols):
                return None
        
        # Calculer les totaux
        autoconsommation_totale = monthly_data['Autoconsommation_kWh'].sum()
        surplus_total = monthly_data['Surplus_kWh'].sum()
        
        # Créer les données pour le camembert
        labels = ['Autoconsommation Locale', 'Surplus Injecté']
        values = [autoconsommation_totale, surplus_total]
        colors = ['#2ca02c', '#ff7f0e']  # Vert pour autoconsommation, orange pour surplus
        
        # Calculer le taux d'autoconsommation
        production_totale = autoconsommation_totale + surplus_total
        taux_autoconsommation = (autoconsommation_totale / production_totale * 100) if production_totale > 0 else 0
        
        # Créer le graphique
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            textinfo='value+percent',
            insidetextorientation='radial',
            hoverinfo='label+value+percent',
            hole=0.4
        )])
        
        # Ajouter une annotation au centre pour le taux d'autoconsommation
        fig.add_annotation(
            text=f"{taux_autoconsommation:.1f}%<br>Autoconsommation",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False
        )
        
        # Mise en page
        fig.update_layout(
            title="Répartition de l'Énergie Produite",
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.1,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
    
    def create_facture_comparison_chart(self, results_data, config):
        """
        Crée un graphique comparant la facture annuelle avec et sans ACOC.
        
        Args:
            results_data: Dictionnaire contenant les résultats financiers
            config: Dictionnaire de configuration
        
        Returns:
            Figure: Objet figure plotly
        """
        if not results_data or 'monthly_data' not in results_data:
            return None
        
        monthly_data = results_data.get('monthly_data')
        if not isinstance(monthly_data, pd.DataFrame) or monthly_data.empty:
            return None
        
        # Récupérer les prix
        prix_optimal = results_data.get('prix_revente', 0)
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        
        # Calculer la consommation annuelle et l'autoconsommation
        if 'Autoconsommation_kWh' in monthly_data.columns and 'Consommation_kWh' in monthly_data.columns:
            autoconsommation_annuelle = monthly_data['Autoconsommation_kWh'].sum()
            consommation_annuelle = monthly_data['Consommation_kWh'].sum()
        else:
            # Tentative alternative avec d'autres noms de colonnes possibles
            alt_cols = {
                'Autoconsommation_kWh': ['autoconsumption_kwh', 'autoconsommation_kwh'],
                'Consommation_kWh': ['consumption_kwh', 'consommation_kwh']
            }
            
            for required, alternatives in alt_cols.items():
                if required not in monthly_data.columns:
                    for alt in alternatives:
                        if alt in monthly_data.columns:
                            monthly_data[required] = monthly_data[alt]
                            break
            
            # Vérifier à nouveau après tentative de correction
            if 'Autoconsommation_kWh' not in monthly_data.columns or 'Consommation_kWh' not in monthly_data.columns:
                return None
        
            autoconsommation_annuelle = monthly_data['Autoconsommation_kWh'].sum()
            consommation_annuelle = monthly_data['Consommation_kWh'].sum()
        
        # Calculer les factures
        # Facture standard EDF
        facture_edf = consommation_annuelle * tarif_edf
        
        # Facture avec ACOC
        facture_autoconso = autoconsommation_annuelle * prix_optimal
        # Le reste de la consommation reste au tarif EDF (si consommation > autoconsommation)
        reste_consommation = max(0, consommation_annuelle - autoconsommation_annuelle)
        facture_reste_edf = reste_consommation * tarif_edf
        facture_totale_acoc = facture_autoconso + facture_reste_edf
        
        # Économie réalisée
        economie = facture_edf - facture_totale_acoc
        pourcentage_economie = (economie / facture_edf) * 100 if facture_edf > 0 else 0
        
        # Créer le graphique de comparaison des factures
        fig = go.Figure()
        
        # Créer les composants pour la facture EDF standard (une seule partie)
        fig.add_trace(go.Bar(
            x=['Facture Standard EDF'],
            y=[facture_edf],
            name='Tarif EDF Standard',
            marker_color='#d62728',  # Rouge pour EDF
            text=[f"{facture_edf:.0f} €"],
            textposition='auto'
        ))
        
        # Créer les composants pour la facture avec ACOC (deux parties)
        fig.add_trace(go.Bar(
            x=['Facture avec ACOC'],
            y=[facture_autoconso],
            name='Partie Autoconsommation',
            marker_color='#2ca02c',  # Vert pour autoconsommation
            text=[f"{facture_autoconso:.0f} €"],
            textposition='inside'
        ))
        
        if reste_consommation > 0:
            fig.add_trace(go.Bar(
                x=['Facture avec ACOC'],
                y=[facture_reste_edf],
                name='Partie Restante EDF',
                marker_color='#ff7f0e',  # Orange pour reste EDF
                text=[f"{facture_reste_edf:.0f} €"],
                textposition='inside'
            ))
        
        # Ajouter une annotation pour l'économie
        fig.add_annotation(
            x=0.5,
            y=max(facture_edf, facture_totale_acoc) * 1.1,
            text=f"Économie: {economie:.0f} € ({pourcentage_economie:.1f}%)",
            showarrow=False,
            font=dict(
                size=14,
                color="#2ca02c"  # Vert pour l'économie
            )
        )
        
        # Mise en page
        fig.update_layout(
            title="Comparaison de Facture Annuelle d'Électricité",
            yaxis_title="Montant Annuel (€)",
            barmode='stack',
            showlegend=True,
            height=450,
            yaxis=dict(tickformat=",.0f €"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
    
    # ==========================================================================
    # GRAPHIQUES POUR LA SECTION PRODUCER
    # ==========================================================================
    
    def create_financial_indicators_chart(self, results):
        """
        Crée un graphique des indicateurs financiers annuels.
        
        Args:
            results: Dictionnaire contenant les résultats financiers détaillés 
                     (normalement issu de indicateurs_au_prix_optimal).
            
        Returns:
            Figure: Objet figure plotly ou None si aucun résultat n'est disponible
        """
        # Vérification initiale des données passées en argument
        if not results or not isinstance(results, dict) or 'monthly_data' not in results:
            st.warning("Données financières invalides ou manquantes pour create_financial_indicators_chart.")
            return None
        
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty:
            st.warning("DataFrame mensuel invalide ou vide.")
            return None
        
        # --- Logique d'agrégation annuelle --- 
        try:
            if not isinstance(monthly_df.index, pd.DatetimeIndex):
                 try: monthly_df.index = pd.to_datetime(monthly_df.index)
                 except: st.error("Impossible de convertir l'index en DatetimeIndex."); return None
                 
            # Agréger par année
            # Utiliser .sum() pour les flux, on pourrait utiliser .last() pour les soldes si besoin
            annual_data = monthly_df.resample('YE').sum()
            annual_data['Year'] = annual_data.index.year # Ajouter colonne Année pour l'axe X
            
            # --- Vérifier l'existence des colonnes nécessaires --- 
            required_cols_plot = ['Revenus_Total', 'OPEX', 'FCFE', 'EBITDA', 'Service_Dette', 'Impots_Provisionnes']
            # Ajouter DSCR si on le calcule annuellement ici (plus simple de le récupérer globalement si possible)
            
            missing_cols_plot = [col for col in required_cols_plot if col not in annual_data.columns]
            if missing_cols_plot:
                 st.warning(f"Colonnes manquantes pour le graphique de flux: {missing_cols_plot}")
                 # Option: essayer de recalculer FCFE ou autres si possible ?
                 # Calcul FCFE annuel si possible:
                 if 'Resultat_Net' in annual_data.columns and 'Amortissement' in annual_data.columns and 'Principal_Rembourse' in annual_data.columns:
                     annual_data['FCFE'] = annual_data['Resultat_Net'] + annual_data['Amortissement'] - annual_data['Principal_Rembourse']
                     if 'FCFE' in missing_cols_plot: missing_cols_plot.remove('FCFE')
                 if missing_cols_plot: # Si toujours manquant après tentative
                     return None # Ne pas générer le graphique
                     
            # Ajouter calcul FCFE cumulé
            if 'FCFE' in annual_data.columns:
                 annual_data['Cumulative_FCFE'] = annual_data['FCFE'].cumsum()
            else: annual_data['Cumulative_FCFE'] = 0
            
            # Calcul DSCR Annuel (si besoin)
            # Vérifier si Tax_Payment existe (nouvelle colonne après refactoring impôts)
            if 'Tax_Payment' in annual_data.columns:
                annual_data['CADS'] = annual_data['EBITDA'] - annual_data['Tax_Payment'] # Utilise le paiement effectif
            else:
                # Fallback si Tax_Payment n'est pas là (ex: ancien calcul) ou pour robustesse
                # On approxime CADS par EBITDA, moins précis mais évite le crash
                st.warning("Colonne 'Tax_Payment' non trouvée pour calcul CADS annuel. Approximation CADS = EBITDA.")
                annual_data['CADS'] = annual_data['EBITDA']

            # Calcul DSCR basé sur CADS calculé ci-dessus
            annual_data['DSCR_Calculated'] = np.where(
                np.abs(annual_data['Service_Dette']) > 1e-9, # Diviseur non nul
                annual_data['CADS'] / annual_data['Service_Dette'],
                np.inf # Cas où Service Dette = 0
            )
            # Gérer le cas 0/0 -> NaN ou autre valeur selon la convention souhaitée
            annual_data.loc[(
                (annual_data['CADS'] <= 0) & (np.abs(annual_data['Service_Dette']) <= 1e-9)),
                'DSCR_Calculated'
            ] = np.nan # CADS <= 0 et Service Dette = 0 -> NaN
                 
        except Exception as e_agg:
            st.error(f"Erreur lors de l'agrégation annuelle pour le graphique: {e_agg}")
            return None
        
        # --- Création du graphique --- 
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.15, # Un peu plus d'espace
            subplot_titles=("Flux Financiers Annuels", "DSCR Annuel")
        )
        
        # --- Sous-graphique 1: Flux financiers --- 
        fig.add_trace(
            go.Bar(x=annual_data['Year'], y=annual_data['Revenus_Total'], name='Revenus', marker_color='#2ca02c'), # Vert
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(x=annual_data['Year'], y=annual_data['OPEX'], name='OPEX', marker_color='#ff7f0e'), # Orange
            row=1, col=1
        )
        # Ajouter EBITDA en ligne ? 
        # fig.add_trace(
        #     go.Scatter(x=annual_data['Year'], y=annual_data['EBITDA'], name='EBITDA', mode='lines', line=dict(color='#1f77b4')), # Bleu
        #     row=1, col=1
        # )
        fig.add_trace(
            go.Scatter(x=annual_data['Year'], y=annual_data['FCFE'], name='FCFE', mode='lines+markers', line=dict(color='#9467bd'), marker=dict(symbol='circle')), # Violet
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=annual_data['Year'], y=annual_data['Cumulative_FCFE'], name='FCFE Cumulé', mode='lines+markers', line=dict(color='#d62728'), marker=dict(symbol='diamond')), # Rouge
            row=1, col=1
        )
        
        # --- Sous-graphique 2: DSCR --- 
        fig.add_trace(
            go.Scatter(x=annual_data['Year'], y=annual_data['DSCR_Calculated'], name='DSCR', mode='lines+markers', line=dict(color='#17becf')), # Cyan
            row=2, col=1
        )
        
        # Ajouter ligne DSCR cible
        target_dscr = st.session_state.config.get('target_dscr', 1.2)
        fig.add_shape(
            type="line", layer='below',
            x0=annual_data['Year'].min(), y0=target_dscr,
            x1=annual_data['Year'].max(), y1=target_dscr,
            line=dict(color="#ff7f0e", width=2, dash="dash"),
            row=2, col=1
        )
        fig.add_annotation(
             x=annual_data['Year'].max(), y=target_dscr, text=f"Cible DSCR: {target_dscr}",
             showarrow=False, yshift=10, xanchor='right', font=dict(color="#ff7f0e"),
            row=2, col=1
        )
        
        # --- Mise en page --- 
        fig.update_layout(
            height=650,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            barmode='relative' # Pour les barres OPEX/Revenus
        )
        fig.update_yaxes(title_text="Montant (€)", row=1, col=1)
        fig.update_yaxes(title_text="DSCR", range=[0, max(2.5, annual_data['DSCR_Calculated'].max()*1.1 if annual_data['DSCR_Calculated'].notna().any() else 2.5)], row=2, col=1)
        fig.update_xaxes(title_text="Année", row=2, col=1)
        
        return fig
    
    def create_waterfall_cashflow_chart(self, results, year_index=4):
        """
        Crée un graphique en cascade pour une année spécifique.
        
        Args:
            results: Dictionnaire contenant les résultats financiers
            year_index: Indice de l'année à analyser (par défaut: 5ème année, donc index 4)
            
        Returns:
            Figure: Objet figure plotly
        """
        if not results or 'monthly_data' not in results:
            return None
        
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty:
            return None
        
        try:
            # Assurer un index Datetime
            if not isinstance(monthly_df.index, pd.DatetimeIndex):
                try:
                    monthly_df.index = pd.to_datetime(monthly_df.index)
                except:
                    return None
        
            # Agréger par année
            annual_data = monthly_df.resample('YE').sum()
            
            # Récupérer les années disponibles
            years = annual_data.index.year.tolist()
            if len(years) <= year_index:
                # Si l'indice demandé est trop grand, utiliser le dernier disponible
                year_index = len(years) - 1
            
            # Vérifier les colonnes requises
            required_comps = ['Revenus_Autoconsommation', 'Revenus_Surplus', 'OPEX', 'Service_Dette', 'Impots_Provisionnes']
            for col in required_comps:
                if col not in annual_data.columns:
                    # Tentative de calcul si manquant
                    if col == 'Revenus_Total' and 'Revenus_Autoconsommation' in annual_data.columns and 'Revenus_Surplus' in annual_data.columns:
                        annual_data['Revenus_Total'] = annual_data['Revenus_Autoconsommation'] + annual_data['Revenus_Surplus']
                    else:
                        st.warning(f"Composante {col} manquante pour le graphique cascade")
            
            # Extraire les données pour l'année sélectionnée
            year_data = annual_data.iloc[year_index]
            selected_year = years[year_index]
            
            # --- Calculer la somme des paiements d'impôts pour CETTE année ---
            annual_tax_payment = 0.0
            if 'Tax_Payment' in year_data:
                 # Somme des paiements trimestriels de cette année (déjà agrégé annuellement)
                 annual_tax_payment = year_data['Tax_Payment']

            # --- Préparer les données pour le graphique en cascade ---
            components = []
            values = []
            
            # Revenus d'autoconsommation
            if 'Revenus_Autoconsommation' in year_data:
                components.append("Revenus Autoconsommation")
                values.append(year_data['Revenus_Autoconsommation'])
            
            # Revenus de surplus
            if 'Revenus_Surplus' in year_data:
                components.append("Revenus Surplus")
                values.append(year_data['Revenus_Surplus'])
            
            # OPEX (négatif)
            if 'OPEX' in year_data:
                components.append("OPEX")
                values.append(-year_data['OPEX'])
            
            # Service de la dette (négatif)
            if 'Service_Dette' in year_data and abs(year_data['Service_Dette']) > 1e-6:
                components.append("Service de la Dette")
                values.append(-year_data['Service_Dette'])
            
            # Impôts (négatif)
            if 'Impots_Provisionnes' in year_data:
                components.append("Impôts")
                values.append(-annual_tax_payment) # Utiliser la somme des paiements effectifs
            
            # Cash-flow net (sera calculé automatiquement par le waterfall)
            components.append("Cash-flow Net")
            
            # Créer le graphique en cascade
            fig = go.Figure(go.Waterfall(
                name="Cascade Cash-flow",
                orientation="v",
                measure=["relative"] * (len(components) - 1) + ["total"],
                x=components,
                textposition="outside",
                text=[f"{abs(val):,.0f}€" for val in values] + [""],
                y=values,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#FF4136"}},  # Rouge pour les valeurs négatives
                increasing={"marker": {"color": "#3D9970"}},  # Vert pour les valeurs positives
                totals={"marker": {"color": "#1E88E5"}}       # Bleu pour le total
            ))
        
        except Exception as e:
            st.error(f"Erreur lors de la création du graphique cascade: {e}")
            return None
        
        # Mise en page
        fig.update_layout(
                title=f"Cascade du Cash-flow - Année {selected_year}",
                showlegend=False,
                height=500,
                xaxis_title="Composantes",
                yaxis_title="Montant (€)",
                yaxis=dict(
                    tickformat=",d €"
                )
            )
            
        return fig
    
    def create_debt_balance_chart(self, results):
        """Crée un graphique de l'évolution du solde de la dette."""
        if not results or 'monthly_data' not in results:
            return None
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty or 'Solde_Dette_Fin_Mois' not in monthly_df.columns:
            return None

        # Assurer un index Datetime pour le graphique
        if not isinstance(monthly_df.index, pd.DatetimeIndex):
            if 'Temps' in monthly_df.columns:
                 monthly_df_chart = monthly_df.set_index('Temps')
                 monthly_df_chart.index = pd.to_datetime(monthly_df_chart.index)
            else: # Essayer de convertir l'index existant
                 try:
                      monthly_df_chart = monthly_df.copy()
                      monthly_df_chart.index = pd.to_datetime(monthly_df_chart.index)
                 except Exception:
                      st.error("Impossible de créer un index de temps pour le graphique de dette.")
                      return None
        else:
            monthly_df_chart = monthly_df

        fig = px.line(
            monthly_df_chart,
            y='Solde_Dette_Fin_Mois',
            title="Évolution du Solde de la Dette Restante",
            labels={'index': 'Date', 'Solde_Dette_Fin_Mois': 'Solde Restant Dû (€)'},
            markers=False # Optionnel: ajouter des marqueurs si peu de points
        )
        fig.update_layout(yaxis_tickformat=",.0f") # Format €
        return fig
    
    def create_annual_revenue_breakdown_chart(self, results):
        """Crée un graphique en barres empilées de la répartition annuelle des revenus."""
        if not results or 'monthly_data' not in results:
            return None
        monthly_df = results.get('monthly_data')
        if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty:
             return None
        required_cols = ['Revenus_Autoconsommation', 'Revenus_Surplus']
        if not all(col in monthly_df.columns for col in required_cols):
            return None

        # Assurer un index Datetime pour le regroupement annuel
        if not isinstance(monthly_df.index, pd.DatetimeIndex):
            if 'Temps' in monthly_df.columns:
                 monthly_df_agg = monthly_df.set_index('Temps')
                 monthly_df_agg.index = pd.to_datetime(monthly_df_agg.index)
            else:
                 try: # Essayer index
                      monthly_df_agg = monthly_df.copy()
                      monthly_df_agg.index = pd.to_datetime(monthly_df_agg.index)
                 except Exception: return None
        else:
            monthly_df_agg = monthly_df

        # Agréger par année
        annual_revenues = monthly_df_agg[required_cols].resample('YE').sum() # YE = Year End frequency
        annual_revenues.index = annual_revenues.index.year # Utiliser juste l'année comme index

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=annual_revenues.index,
            y=annual_revenues['Revenus_Autoconsommation'],
            name='Revenus Autoconsommation',
            marker_color='rgb(31, 119, 180)' # Bleu
        ))
        fig.add_trace(go.Bar(
            x=annual_revenues.index,
            y=annual_revenues['Revenus_Surplus'],
            name='Revenus Surplus (OA)',
            marker_color='rgb(255, 127, 14)' # Orange
        ))

        fig.update_layout(
            barmode='stack', # Empiler les barres
            title="Répartition Annuelle des Revenus",
            xaxis_title="Année",
            yaxis_title="Revenus Annuels (€)",
            legend_title="Source de Revenus",
            yaxis_tickformat=",.0f" # Format €
        )
        return fig

    def create_monte_carlo_results_chart(self, mc_results):
        """
        Crée un graphique des résultats de la simulation Monte Carlo.
        
        Args:
            mc_results: Dictionnaire contenant les résultats MC pour un scénario.
            
        Returns:
            Figure: Objet figure plotly ou None si aucun résultat n'est disponible
        """
        # Vérifier les résultats MC passés en argument
        if not mc_results or not isinstance(mc_results, dict) or 'probabilities' not in mc_results or 'results' not in mc_results or 'statistics' not in mc_results:
            st.warning("Données Monte Carlo invalides ou manquantes pour create_monte_carlo_results_chart.")
            return None
        
        # Utiliser 'results' (valeurs brutes) et 'statistics' du dict mc_results
        raw_values = mc_results.get('results', {})
        stats = mc_results.get('statistics', {})
        contraintes_mc = mc_results.get('contraintes_mc', {})
        scenario_name = mc_results.get('scenario_name', 'Inconnu')
        
        # --- Créer le graphique --- 
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Distribution VAN Equity (€)", "Distribution TRI Equity (%)", "Distribution Payback Equity (ans)", "Distribution DSCR Moyen"),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # --- Configurer les métriques à afficher --- 
        metrics_to_plot = [
            {'key': 'npv', 'name': 'VAN Equity (€)', 'unit': '€', 'multiplier': 1, 'row': 1, 'col': 1, 'color': '#1f77b4', 'target': 0},
            {'key': 'irr', 'name': 'TRI Equity (%)', 'unit': '%', 'multiplier': 100, 'row': 1, 'col': 2, 'color': '#2ca02c', 'target': st.session_state.config.get('cout_fonds_propres', 8.0)},
            {'key': 'payback_period', 'name': 'Payback Equity (ans)', 'unit': 'ans', 'multiplier': 1, 'row': 2, 'col': 1, 'color': '#ff7f0e', 'target': contraintes_mc.get('payback_max')},
            {'key': 'avg_dscr', 'name': 'DSCR Moyen', 'unit': None, 'multiplier': 1, 'row': 2, 'col': 2, 'color': '#d62728', 'target': contraintes_mc.get('dscr_min')}
        ]
        
        for metric in metrics_to_plot:
            metric_key = metric['key']
            values_key = f"{metric_key}_values"
            if values_key not in raw_values or metric_key not in stats:
                 print(f"WARN MC Plot: Données manquantes pour {metric_key}")
                 continue # Passer à la métrique suivante si données manquantes
                 
            data_values = np.array(raw_values[values_key])
            data_values = data_values[np.isfinite(data_values)] # Garder uniquement les finis pour l'histogramme
            stat_info = stats[metric_key]
            mean_val = stat_info.get('mean', np.nan)
            target_val = metric.get('target')
            
            # Histogramme
            fig.add_trace(
                go.Histogram(
                        x=data_values * metric['multiplier'], 
                        name=metric['name'],
                        marker_color=metric['color'],
                        opacity=0.75, nbinsx=30
                    ),
                    row=metric['row'], col=metric['col']
                )
            
            # Ligne moyenne
            if pd.notna(mean_val):
                 mean_plot = mean_val * metric['multiplier']
                 fig.add_vline(x=mean_plot, line_width=2, line_dash="dash", line_color="#8c564b", # Marron
                              annotation_text=f"Moy: {mean_plot:.2f}{metric.get('unit','')}", 
                              annotation_position="top right", row=metric['row'], col=metric['col'])
            
            # Ligne cible
            if target_val is not None and pd.notna(target_val):
                 target_plot = target_val * metric['multiplier']
                 color_cible = "#2ca02c" # Vert par défaut
                 # Inverser couleur si objectif est un maximum (Payback)
                 if metric_key == 'payback_period': color_cible = "#d62728" # Rouge
                 fig.add_vline(x=target_plot, line_width=2, line_dash="dot", line_color=color_cible,
                              annotation_text=f"Cible: {target_plot:.2f}{metric.get('unit','')}", 
                              annotation_position="bottom right", row=metric['row'], col=metric['col'])
                              
            # Mise à jour axes
            fig.update_xaxes(title_text=metric['name'], row=metric['row'], col=metric['col'])
            fig.update_yaxes(title_text="Fréquence", row=metric['row'], col=metric['col'])

        # --- Mise en page globale --- 
        fig.update_layout(
            title_text=f"Distributions Monte Carlo - Scénario: {scenario_name}",
            height=700,
            showlegend=False,
            bargap=0.1
        )
        return fig
    
    def create_monte_carlo_boxplot(self, mc_results):
        """Crée des box plots pour les résultats clés de Monte Carlo."""
        if not mc_results or 'results' not in mc_results or 'statistics' not in mc_results:
             return None

        data = mc_results.get('results', {})
        stats = mc_results.get('statistics', {})
        metrics_to_plot = {
            'npv': {'name': 'VAN (€)', 'data_key': 'npv_values'},
            'irr': {'name': 'TRI (%)', 'data_key': 'irr_values', 'multiplier': 100},
            'payback_period': {'name': 'Payback Equity (ans)', 'data_key': 'payback_period_values'},
            'avg_dscr': {'name': 'DSCR Moyen', 'data_key': 'avg_dscr_values'}
        }

        fig = go.Figure()

        for key, info in metrics_to_plot.items():
            values = data.get(info['data_key'])
            if values is not None:
                # Nettoyer les NaN et Inf avant le boxplot
                valid_values = np.array(values)
                valid_values = valid_values[np.isfinite(valid_values)]
                if len(valid_values) > 0:
                    multiplier = info.get('multiplier', 1)
                    fig.add_trace(go.Box(
                        y=valid_values * multiplier,
                        name=info['name'],
                        boxpoints='outliers', # Afficher les outliers
                        jitter=0.3, # un peu de dispersion pour les outliers
                        pointpos=-1.8 # positionner les outliers
                    ))

        fig.update_layout(
            title="Distribution des Résultats Clés (Monte Carlo)",
            yaxis_title="Valeur",
            showlegend=False # Légende pas très utile pour box plots simples
        )
        return fig
    
    def create_sensitivity_tornado_chart(self, base_result, sensitivity_results):
        """
        Crée un graphique Tornado montrant l'impact des variations des paramètres.
        
        Args:
            base_result: Résultat du cas de base
            sensitivity_results: Dictionnaire {param_name: {param_value: results}}
            
        Returns:
            Figure: Objet figure plotly
        """
        if not base_result or not sensitivity_results:
            return None
        
        # Vérifier que le base_result a les indicateurs clés
        if 'npv' not in base_result or 'irr' not in base_result:
            return None
        
        # Valeurs de base pour les métriques d'intérêt
        base_npv = base_result.get('npv', 0)
        base_irr = base_result.get('irr', 0) * 100  # Convertir en %
        
        # Préparer les données pour le graphique tornado
        tornado_data = []
        
        # Pour chaque paramètre
        for param, results in sensitivity_results.items():
            param_values = []
            npv_deltas = []
            irr_deltas = []
            
            # Pour chaque valeur du paramètre
            for value, result in results.items():
                if 'npv' in result and 'irr' in result:
                    param_values.append(value)
                    npv_deltas.append(result['npv'] - base_npv)
                    irr_deltas.append(result['irr'] * 100 - base_irr)  # Convertir en %
            
            if param_values:
                tornado_data.append({
                    'parameter': param,
                    'min_npv_delta': min(npv_deltas),
                    'max_npv_delta': max(npv_deltas),
                    'min_irr_delta': min(irr_deltas),
                    'max_irr_delta': max(irr_deltas)
                })
        
        if not tornado_data:
            return None
        
        # Créer le graphique tornado
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Impact sur la VAN (€)", "Impact sur le TRI (%)"),
            horizontal_spacing=0.1
        )
        
        # Trier les paramètres par impact sur la VAN
        tornado_data.sort(key=lambda x: abs(x['max_npv_delta'] - x['min_npv_delta']), reverse=True)
        parameters = [item['parameter'] for item in tornado_data]
        
        # Graphique pour la VAN
        fig.add_trace(
            go.Bar(
                y=parameters,
                x=[item['min_npv_delta'] for item in tornado_data],
                orientation='h',
                name='Impact Négatif VAN',
                marker=dict(color='rgba(255, 65, 54, 0.7)'),
                showlegend=True
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                y=parameters,
                x=[item['max_npv_delta'] for item in tornado_data],
                orientation='h',
                name='Impact Positif VAN',
                marker=dict(color='rgba(61, 153, 112, 0.7)'),
                showlegend=True
            ),
            row=1, col=1
        )
        
        # Graphique pour le TRI
        fig.add_trace(
            go.Bar(
                y=parameters,
                x=[item['min_irr_delta'] for item in tornado_data],
                orientation='h',
                name='Impact Négatif TRI',
                marker=dict(color='rgba(255, 65, 54, 0.7)'),
                showlegend=False
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(
                y=parameters,
                x=[item['max_irr_delta'] for item in tornado_data],
                orientation='h',
                name='Impact Positif TRI',
                marker=dict(color='rgba(61, 153, 112, 0.7)'),
                showlegend=False
            ),
            row=1, col=2
        )
        
        # Mise en page
        fig.update_layout(
            barmode='relative',
            height=500,
            title="Analyse de Sensibilité (Tornado)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_xaxes(title_text="Variation VAN (€)", row=1, col=1)
        fig.update_xaxes(title_text="Variation TRI (%)", row=1, col=2)
        fig.update_yaxes(title_text="Paramètre", row=1, col=1)
        fig.update_yaxes(title_text="", row=1, col=2)
        
        return fig
    
    def display_sensitivity_analysis(self, results_base, results_sensitivity, selected_params=None):
        """
        Affiche l'analyse de sensibilité pour les paramètres sélectionnés.
        
        Args:
            results_base: Résultats du cas de base
            results_sensitivity: Dictionnaire {param_name: {param_value: results}}
            selected_params: Liste des paramètres à afficher (si None, tous)
        """
        if not results_base or not results_sensitivity:
            st.warning("Données insuffisantes pour l'analyse de sensibilité.")
            return
        
        if not selected_params:
            selected_params = list(results_sensitivity.keys())
        
        # Afficher le graphique Tornado si plus de 2 paramètres
        if len(selected_params) > 2:
            tornado_fig = self.create_sensitivity_tornado_chart(results_base, results_sensitivity)
            if tornado_fig:
                st.plotly_chart(tornado_fig, use_container_width=True)
            else:
                st.warning("Impossible de créer le graphique Tornado.")
        
        # Pour chaque paramètre, créer un graphique individuel
        for param in selected_params:
            if param in results_sensitivity:
                results = results_sensitivity[param]
                
                # Créer un DataFrame pour le paramètre
                param_values = []
                npv_values = []
                irr_values = []
                
                for value, result in results.items():
                    if 'npv' in result and 'irr' in result:
                        param_values.append(value)
                        npv_values.append(result['npv'])
                        irr_values.append(result['irr'] * 100)  # Convertir en %
                
                if param_values:
                    # Créer le graphique
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    fig.add_trace(
                        go.Scatter(
                            x=param_values,
                            y=npv_values,
                            name="VAN (€)",
                            line=dict(color='#1f77b4', width=3),
                            mode='lines+markers'
                        ),
                        secondary_y=False
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=param_values,
                            y=irr_values,
                            name="TRI (%)",
                            line=dict(color='#2ca02c', width=3),
                            mode='lines+markers'
                        ),
                        secondary_y=True
                    )
                    
                    # Mise en page
                    fig.update_layout(
                        title=f"Sensibilité au paramètre: {param}",
                        xaxis_title=f"Valeur du paramètre",
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        height=400,
                        hovermode="x unified"
                    )
                    
                    fig.update_yaxes(title_text="VAN (€)", secondary_y=False)
                    fig.update_yaxes(title_text="TRI (%)", secondary_y=True)
                    
            st.plotly_chart(fig, use_container_width=True)
            
    def display_sensitivity_analysis_section(self, selected_scenario):
        """
        Affiche la section d'analyse de sensibilité pour le scénario sélectionné.
        
        Args:
            selected_scenario: Nom du scénario à analyser
        """
        optim_results_base = st.session_state.constrained_optim_results[selected_scenario]
        base_results = optim_results_base.get('indicateurs_au_prix_optimal')
        if not base_results or 'monthly_data' not in base_results: 
            st.error(f"Indicateurs manquants pour scénario de base {selected_scenario}."); 
            return
        
        # Récupérer les scénarios avec résultats
        scenarios_with_results = [s for s in st.session_state.get('scenarios', {}).keys() 
                                  if s in st.session_state.get('constrained_optim_results', {}) and 
                                  st.session_state.constrained_optim_results[s].get('indicateurs_au_prix_optimal')]
        if not scenarios_with_results:
            st.info("Aucun scénario valide trouvé pour comparaison.")
            return
            
        # Extraire les données annuelles du scénario de base
        try:
            monthly_df_base = base_results['monthly_data']
            if not isinstance(monthly_df_base.index, pd.DatetimeIndex):
                 monthly_df_base = monthly_df_base.set_index(pd.to_datetime(monthly_df_base.index))
            annual_data_base = monthly_df_base.resample('YE').sum() # Ou autre agrégation si nécessaire
            
            required_cols_sens = ['Resultat_Net', 'FCFE'] # Définir les colonnes nécessaires
            
            # Tentative de calcul FCFE si manquant dans base_results
            if 'FCFE' not in annual_data_base.columns and all(col in annual_data_base.columns for col in ['Resultat_Net', 'Amortissement', 'Principal_Rembourse']):
                annual_data_base['FCFE'] = annual_data_base['Resultat_Net'] + annual_data_base['Amortissement'] - annual_data_base['Principal_Rembourse']
            
            # Vérification finale des colonnes requises dans base_results
            if not all(col in annual_data_base.columns for col in required_cols_sens):
                 missing = [col for col in required_cols_sens if col not in annual_data_base.columns]
                 st.error(f"Impossible de continuer l'analyse de sensibilité sans les colonnes de base: {missing}")
                 return
                 
        except Exception as e_annual_base:
             st.error(f"Erreur préparation données annuelles pour scénario de base {selected_scenario}: {e_annual_base}")
             return

        # Boucle sur les autres scénarios
        comparison_data = {}
        for scenario_name in scenarios_with_results:
            if scenario_name == selected_scenario: 
                continue 
            
            optim_results_comp = st.session_state.constrained_optim_results.get(scenario_name, {})
            comp_results = optim_results_comp.get('indicateurs_au_prix_optimal')
            
            if comp_results and isinstance(comp_results.get('monthly_data'), pd.DataFrame):
                try:
                    monthly_df_comp = comp_results['monthly_data']
                    if not isinstance(monthly_df_comp.index, pd.DatetimeIndex):
                         monthly_df_comp = monthly_df_comp.set_index(pd.to_datetime(monthly_df_comp.index))
                    
                    annual_data_comp = monthly_df_comp.resample('YE').sum()
                    
                    if 'FCFE' not in annual_data_comp.columns and all(col in annual_data_comp.columns for col in ['Resultat_Net', 'Amortissement', 'Principal_Rembourse']):
                        annual_data_comp['FCFE'] = annual_data_comp['Resultat_Net'] + annual_data_comp['Amortissement'] - annual_data_comp['Principal_Rembourse']

                    if all(col in annual_data_comp.columns for col in required_cols_sens):
                        common_years = annual_data_base.index.intersection(annual_data_comp.index)
                        if not common_years.empty:
                             comparison_data[scenario_name] = annual_data_comp.loc[common_years, required_cols_sens]
                        
                except Exception as e_annual_comp:
                     print(f"WARN Sensibilité: Erreur traitement données annuelles scénario {scenario_name}: {e_annual_comp}")

        # Afficher les différences ou un graphique de comparaison
        if not comparison_data:
            st.info("Aucun scénario comparable trouvé avec les données nécessaires (Resultat_Net, FCFE). Vérifiez les logs pour plus de détails.")
            return

        try:
            first_comp_scenario = list(comparison_data.keys())[0]
            df_comp = comparison_data[first_comp_scenario]
            
            common_index_for_diff = annual_data_base.index.intersection(df_comp.index)
            if not common_index_for_diff.empty:
                df_base_aligned = annual_data_base.loc[common_index_for_diff, required_cols_sens]
                df_comp_aligned = df_comp.loc[common_index_for_diff] 
                
                df_diff = df_comp_aligned - df_base_aligned
                
                st.markdown(f"**Différence Annuelle ({first_comp_scenario} vs {selected_scenario})**")
                st.dataframe(df_diff)
            else:
                st.warning(f"Aucune année commune pour calculer la différence avec {first_comp_scenario}.")
        except Exception as e_display_diff:
            st.error(f"Erreur lors de l'affichage de la différence de sensibilité: {e_display_diff}")

    def create_cumulative_savings_chart(self, results_data, config):
        """
        Crée un graphique montrant les économies cumulées sur plusieurs années.
        
        Args:
            results_data: Dictionnaire contenant les résultats financiers
            config: Dictionnaire de configuration
            
        Returns:
            Figure: Objet figure plotly
        """
        if not results_data or 'monthly_data' not in results_data:
            return None
        
        monthly_data = results_data.get('monthly_data')
        if not isinstance(monthly_data, pd.DataFrame) or monthly_data.empty:
            return None
        
        # Récupérer les prix
        # Le prix de vente est celui utilisé pour l'analyse (potentiellement optimisé)
        prix_vente_scenario = results_data.get('prix_revente') 
        if prix_vente_scenario is None:
             # Fallback si prix_revente n'est pas dans les indicateurs (peu probable)
             prix_vente_scenario = config.get('prix_vente_initial', 0.15) 
             
        tarif_edf = config.get('tarif_edf_reference', 0.21)
        taux_inflation = config.get('taux_inflation', 2.0) / 100
        
        # Calculer l'autoconsommation annuelle
        autoconso_col = None
        if 'Autoconsommation_kWh' in monthly_data.columns:
            autoconso_col = 'Autoconsommation_kWh'
        else:
            # Tentative alternative avec d'autres noms de colonnes possibles
            alt_cols = ['autoconsumption_kwh', 'autoconsommation_kwh']
            for alt in alt_cols:
                if alt in monthly_data.columns:
                    autoconso_col = alt
                    break
            else:
                st.warning("Impossible de trouver la colonne d'autoconsommation (ex: 'Autoconsommation_kWh') dans les données mensuelles.")
                return None  # Aucune colonne d'autoconsommation trouvée
        
        # S'assurer que l'index est datetime pour l'agrégation annuelle
        monthly_data_agg = monthly_data
        if not isinstance(monthly_data_agg.index, pd.DatetimeIndex):
            try:
                 monthly_data_agg.index = pd.to_datetime(monthly_data_agg.index)
            except Exception:
                 st.error("Impossible de convertir l'index des données mensuelles en DatetimeIndex.")
                 return None
                 
        # Agréger l'autoconsommation par année
        autoconsommation_par_an = monthly_data_agg[autoconso_col].resample('YE').sum()
        # Prendre la moyenne des années disponibles comme référence stable (évite impact dégradation sur volume)
        autoconsommation_annuelle_ref = autoconsommation_par_an.mean() if not autoconsommation_par_an.empty else 0
        if autoconsommation_annuelle_ref <= 0:
             st.warning("Le volume d'autoconsommation annuel moyen est nul ou négatif.")
             return None

        # Nombre d'années à représenter
        duree_projet = config.get('duree_ppa', 240) // 12  # Conversion mois -> années
        if duree_projet <= 0: duree_projet = 20  # Valeur par défaut
        
        annees = list(range(1, duree_projet + 1))
        economies_annuelles = []
        
        for i in range(duree_projet):
            # Calculer les prix indexés pour l'année i (commençant à l'année 0 pour l'indexation)
            tarif_edf_annee = tarif_edf * (1 + taux_inflation) ** i
            prix_vente_annee = prix_vente_scenario * (1 + taux_inflation) ** i # Indexer aussi le prix de vente
            economie_kwh_annee = tarif_edf_annee - prix_vente_annee
            # Utiliser le volume d'autoconsommation de référence pour l'économie
            economie_annuelle = economie_kwh_annee * autoconsommation_annuelle_ref 
            economies_annuelles.append(economie_annuelle)
        
        economies_cumulees_liste = np.cumsum(economies_annuelles)
        
        # Créer le graphique
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Barres: économies annuelles
        fig.add_trace(
            go.Bar(
                x=annees,
                y=economies_annuelles,
                name="Économie Annuelle",
                marker_color='rgba(44, 160, 44, 0.7)', # Vert transparent
                hovertemplate="Année %{x}<br>Économie: %{y:,.0f} €"
            ),
            secondary_y=False
        )
        
        # Ligne: économies cumulées
        fig.add_trace(
            go.Scatter(
                x=annees,
                y=economies_cumulees_liste,
                name="Économies Cumulées",
                line=dict(color='#d62728', width=3), # Rouge
                mode='lines+markers',
                marker=dict(size=6),
                hovertemplate="Année %{x}<br>Économies Cumulées: %{y:,.0f} €"
            ),
            secondary_y=True
        )
        
        # Annotation économie totale
        if economies_cumulees_liste.size > 0:
             total_savings = economies_cumulees_liste[-1]
             fig.add_annotation(
                 x=duree_projet, y=total_savings, ax=40, ay=-40,
                 text=f"Total sur {duree_projet} ans:<br><b>{total_savings:,.0f} €</b>",
                 showarrow=True, arrowhead=1, arrowsize=1, arrowwidth=1.5, arrowcolor="#d62728",
                 font=dict(size=11, color="#d62728"), bordercolor="#d62728", borderwidth=1, bgcolor="rgba(255,255,255,0.7)", align="left",
                 secondary_y="y2" # S'assurer que l'annotation est liée à l'axe Y secondaire
             )

        # Milestones (adapté)
        milestones = [5, 10, 15]
        for milestone in milestones:
            if 0 < milestone <= len(economies_cumulees_liste):
                milestone_idx = milestone - 1
                fig.add_annotation(
                    x=milestone, y=economies_cumulees_liste[milestone_idx],
                    text=f"{economies_cumulees_liste[milestone_idx]:,.0f}€",
                    showarrow=False, yshift=10, font=dict(size=10, color="#d62728"),
                    secondary_y="y2"
                )
        
        # Mise en page
        fig.update_layout(
            title="Évolution des Économies Estimées sur la Durée du Projet",
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=500, hovermode="x unified"
        )
        fig.update_xaxes(
            title_text="Année", 
            dtick=1 if duree_projet <= 10 else (2 if duree_projet <= 20 else 5)
        )
        fig.update_yaxes(title_text="Économie Annuelle (€)", secondary_y=False, tickformat=",.0f")
        fig.update_yaxes(title_text="Économies Cumulées (€)", secondary_y=True, tickformat=",.0f", 
                         range=[0, total_savings * 1.1] if economies_cumulees_liste.size > 0 else None)
        
        return fig
    
    def create_daily_pattern_chart(self, results: dict | None) -> tuple[go.Figure | None, list[str] | None]:
        """
        Crée le graphique des profils journaliers moyens ET génère des suggestions
        basées sur l'analyse de ces profils.

        Args:
            results: Dictionnaire contenant les résultats ('hourly_aggregated_data').

        Returns:
            Tuple contenant:
            - L'objet Figure Plotly (ou None si erreur).
            - Une liste de strings contenant les suggestions (ou None).
        """
        suggestions = [] # Initialiser la liste des suggestions
        fig = None # Initialiser la figure

        # --- 1. Récupération et Validation des données horaires ---
        if not results or 'hourly_aggregated_data' not in results:
            # Utiliser st.info ou st.warning, pas bloquant ici
            st.info("Données horaires agrégées non trouvées pour l'analyse de profil.")
            return None, None # Retourner None pour fig et suggestions
        df_hourly = results.get('hourly_aggregated_data')
        if not isinstance(df_hourly, pd.DataFrame) or df_hourly.empty:
            st.warning("DataFrame horaire invalide ou vide pour l'analyse de profil.")
            return None, None

        # Ajuster la vérification des colonnes pour utiliser l'index 'Temps'
        df = df_hourly.copy()
        required_cols = ['production_kwh', 'consumption_kwh']
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'Temps' in df.columns:
                if not pd.api.types.is_datetime64_any_dtype(df['Temps']):
                    try:
                        df['Temps'] = pd.to_datetime(df['Temps'], errors='coerce')
                    except Exception as e_time:
                        st.error(f"Impossible de convertir la colonne 'Temps' en datetime: {e_time}")
                        return None, None
                df = df.dropna(subset=['Temps']).set_index('Temps')
            else:
                st.error("Index non Datetime et colonne 'Temps' non trouvée.")
                return None, None
        elif not pd.api.types.is_datetime64_any_dtype(df.index):
             st.error("L'index n'est pas de type Datetime.")
             return None, None

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Colonnes manquantes dans les données horaires : {', '.join(missing_cols)}")
            return None, None

        try:
            # --- S'assurer que les colonnes énergétiques sont numériques ---
            for col in required_cols + ['autoconsumption_kwh', 'surplus_kwh']:
                 if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                      try:
                           df[col] = pd.to_numeric(df[col], errors='coerce')
                      except Exception:
                           st.warning(f"Impossible de convertir la colonne {col} en numérique.")
                           df[col] = 0.0 # Remplacer par 0 en cas d'échec
            df = df.fillna(0.0) # Remplacer NaN éventuels après conversion
            # ------------------------------------------------------------

            df['hour'] = df.index.hour
            if 'autoconsumption_kwh' not in df.columns:
                 df['autoconsumption_kwh'] = np.minimum(df['production_kwh'], df['consumption_kwh'])
            if 'surplus_kwh' not in df.columns:
                 df['surplus_kwh'] = (df['production_kwh'] - df['autoconsumption_kwh']).clip(lower=0)

            # --- 2. Calcul des Moyennes Horaires --- (inchangé)
            hourly_means = df.groupby('hour')[['production_kwh', 'consumption_kwh', 'autoconsumption_kwh', 'surplus_kwh']].mean()
            if len(hourly_means) < 24:
                 hourly_means = hourly_means.reindex(range(24), fill_value=0.0)

            # --- 3. Analyse des Courbes pour Suggestions --- (ajouté/modifié)
            heures_solaires = range(9, 17)
            heures_pic_soir = range(18, 22)
            heures_pic_matin = range(6, 9)
            hourly_means['net_power'] = hourly_means['production_kwh'] - hourly_means['consumption_kwh']
            max_surplus_jour = hourly_means.loc[hourly_means.index.isin(heures_solaires), 'net_power'].clip(lower=0).max()
            avg_prod_jour = hourly_means.loc[hourly_means.index.isin(heures_solaires), 'production_kwh'].mean()
            max_deficit_soir_matin = abs(hourly_means.loc[hourly_means.index.isin(list(heures_pic_soir) + list(heures_pic_matin)), 'net_power'].clip(upper=0).min())
            avg_conso_pics = hourly_means.loc[hourly_means.index.isin(list(heures_pic_soir) + list(heures_pic_matin)), 'consumption_kwh'].mean()
            seuil_surplus_relatif = 0.20
            seuil_deficit_relatif = 0.30
            surplus_significatif = max_surplus_jour > (avg_prod_jour * seuil_surplus_relatif) if avg_prod_jour > 1e-3 else False
            deficit_significatif = max_deficit_soir_matin > (avg_conso_pics * seuil_deficit_relatif) if avg_conso_pics > 1e-3 else False

            suggestions.append("💡 **Analysez les Courbes :** Observez les moments où la production (jaune/or) dépasse la consommation (bleue) et vice-versa.")
            if surplus_significatif:
                suggestions.append(f"☀️ **Fort Surplus Détecté :** Un surplus moyen important (max ~{max_surplus_jour:.1f} kWh/h) est produit en journée. **Priorité : Stockage batterie ou pilotage de charges** (chauffe-eau, VE...) pendant ces heures pour mieux valoriser cette énergie.")
            else:
                 suggestions.append("✔️ **Surplus Journalier Limité :** Le surplus de production en journée semble modéré ou bien absorbé par la consommation. L'impact du stockage/pilotage pourrait être moins important sur ce point.")
            if deficit_significatif:
                suggestions.append(f"🌙 **Fort Déficit Détecté :** Un besoin important d'énergie depuis le réseau (max ~{max_deficit_soir_matin:.1f} kWh/h) apparaît le matin/soir. L'énergie stockée en journée ou le décalage de certaines consommations serait particulièrement utile.")
            else:
                 suggestions.append("✔️ **Déficit Matin/Soir Limité :** Les pointes de consommation matin/soir semblent relativement bien couvertes ou modérées. L'impact du stockage/pilotage sur ces périodes pourrait être moins critique.")
            if surplus_significatif or deficit_significatif:
                 suggestions.append("👥 **Mix Consommateurs :** Envisager d'intégrer des participants avec des profils de consommation complémentaires pourrait aider à équilibrer les flux.")

            # --- 4. Création de la Figure Plotly --- (inchangée)
            fig = go.Figure()
            colors = {'production_kwh': 'gold', 'consumption_kwh': 'blue', 'autoconsumption_kwh': 'green', 'surplus_kwh': 'orange'}
            names = {'production_kwh': 'Production Moyenne', 'consumption_kwh': 'Consommation Moyenne', 'autoconsumption_kwh': 'Autoconsommation Moyenne', 'surplus_kwh': 'Surplus Moyen'}
            for col in ['production_kwh', 'consumption_kwh', 'autoconsumption_kwh', 'surplus_kwh']:
                if col in hourly_means.columns:
                    fig.add_trace(go.Scatter(x=hourly_means.index, y=hourly_means[col], mode='lines+markers', name=names.get(col, col), line=dict(color=colors.get(col, 'grey')), marker=dict(size=6)))
            fig.update_layout(
                title="Profil Journalier Moyen (Agrégé)",
                xaxis_title="Heure de la journée", yaxis_title="Énergie Moyenne (kWh par heure)",
                legend_title="Flux Énergétiques",
                xaxis=dict(tickmode='array', tickvals=list(range(0, 24)), ticktext=[f"{h}h" for h in range(0, 24)]),
                hovermode="x unified"
            )

            return fig, suggestions # Retourner la figure ET les suggestions

        except Exception as e:
            st.error(f"Erreur lors de la création/analyse du profil journalier : {e}")
            return None, None # Retourner None pour les deux

    def show_ui(self):
        """
        Affiche l'interface utilisateur refonte avec deux sections principales:
        1. Synthèse Client
        2. Analyse Producteur/Investisseur
        """
        st.markdown("<h1 class='main-header'>Visualisation des Résultats</h1>", unsafe_allow_html=True)
        
        # --- Vérification Initiale des Données ---
        if not hasattr(st.session_state, 'constrained_optim_results') or not st.session_state.constrained_optim_results:
            st.warning("""
            Pour accéder aux visualisations, vous devez d'abord :
            1. Aller dans l'onglet 'Analyse & Optimisation'
            2. Lancer l'optimisation et obtenir un prix optimal
            """)
            return
        
        # --- Sélection du Scénario ---
        available_scenarios = list(st.session_state.constrained_optim_results.keys())
        if not available_scenarios:
            st.warning("Aucun résultat d'optimisation trouvé.")
            return
            
        default_scenario = available_scenarios[0]
        selected_scenario_idx = 0
        
        if 'selected_scenario_visu' in st.session_state and st.session_state.selected_scenario_visu in available_scenarios:
            selected_scenario_idx = available_scenarios.index(st.session_state.selected_scenario_visu)
            
        selected_scenario = st.selectbox(
            "Sélectionner un scénario à visualiser",
            options=available_scenarios,
            index=selected_scenario_idx,
            key="viz_scenario_select"
        )
        
        st.session_state.selected_scenario_visu = selected_scenario
        
        # --- Récupération des Résultats pour le Scénario Sélectionné ---
        optim_results = st.session_state.constrained_optim_results.get(selected_scenario, {})
        results_data = optim_results.get('indicateurs_au_prix_optimal')
        
        if not results_data or not isinstance(results_data, dict) or 'monthly_data' not in results_data:
            st.warning(f"Données détaillées manquantes pour le scénario '{selected_scenario}'.")
            return
        
        # --- Récupération des Résultats Monte Carlo si disponibles ---
        mc_results = st.session_state.get('monte_carlo_results', {}).get(selected_scenario)
        
        # --- Création des Onglets pour les Deux Sections Principales ---
        client_tab, producer_tab = st.tabs(["📊 Synthèse Client", "📈 Analyse Producteur/Investisseur"])
        
        # --- Section 1: Synthèse Client ---
        with client_tab:
            st.markdown("<h2 class='sub-header'>Synthèse pour le Client Final</h2>", unsafe_allow_html=True)
            st.caption("Ces graphiques présentent les informations clés et les avantages pour un consommateur participant à l'Autoconsommation Collective.")
            
            # Ligne 1: Comparaison Prix et Économies Annuelle (existant)
            col1_1, col1_2 = st.columns(2)
            with col1_1:
                fig_price_comp = self.create_price_comparison_chart(results_data, st.session_state.config)
                if fig_price_comp:
                    st.plotly_chart(fig_price_comp, use_container_width=True)
                else:
                    st.warning("Impossible d'afficher la comparaison de prix.")
            with col1_2:
                fig_savings = self.create_annual_savings_chart(results_data, st.session_state.config)
                if fig_savings:
                    st.plotly_chart(fig_savings, use_container_width=True)
                else:
                    st.warning("Impossible de calculer les économies annuelles.")
            
            st.markdown("---") # Séparateur visuel

            # Ligne 2: Répartition Énergie et Comparaison Facture (Réorganisé)
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                fig_energy_pie = self.create_energy_distribution_pie(results_data)
                if fig_energy_pie:
                    st.plotly_chart(fig_energy_pie, use_container_width=True)
                else:
                    st.warning("Impossible d'afficher la répartition de l'énergie.")
            with col2_2:
                # --- AJOUT : Appel create_facture_comparison_chart --- 
                fig_facture_comp = self.create_facture_comparison_chart(results_data, st.session_state.config)
                if fig_facture_comp:
                     st.plotly_chart(fig_facture_comp, use_container_width=True)
                else:
                     st.warning("Impossible d'afficher la comparaison de facture.")

            st.markdown("---") # Séparateur visuel

            # Ligne 3: Économies Cumulées et Équivalence (Nouveaux graphiques)
            col3_1, col3_2 = st.columns(2)
            with col3_1:
                # --- AJOUT : Appel create_cumulative_savings_chart --- 
                fig_cumul_savings = self.create_cumulative_savings_chart(results_data, st.session_state.config)
                if fig_cumul_savings:
                     st.plotly_chart(fig_cumul_savings, use_container_width=True)
                else:
                     st.warning("Impossible d'afficher les économies cumulées.")
            # Laisser la colonne 3_2 vide pour le moment ou y mettre l'équivalence ? 
            # Mettons l'équivalence ici si elle est sélectionnée dans le selecteur principal
            # ou affichons là aussi ? Pour l'instant, laissons la logique du sélecteur pour l'équivalence.

        # --- Section 2: Analyse Producteur/Investisseur ---
        with producer_tab:
            st.markdown("<h2 class='sub-header'>Analyse pour le Producteur/Investisseur</h2>", unsafe_allow_html=True)
            st.caption("Ces graphiques présentent les analyses détaillées pour évaluer la performance financière et technique du projet.")
            
            # Sous-tabs pour organiser les graphiques producteur
            # Ajout d'un onglet "Profils Énergétiques"
            flux_tab, revenus_tab, dette_tab, profils_tab, mc_tab = st.tabs([
                "Flux Financiers", "Revenus", "Dette", "Profils Énergétiques", "Monte Carlo"
            ])
            
            with flux_tab:
                # Flux Financiers Annuels
                fig_flux = self.create_financial_indicators_chart(results_data)
                if fig_flux:
                    st.plotly_chart(fig_flux, use_container_width=True)
                else:
                    st.warning("Impossible de générer le graphique des flux financiers.")
                
                # Cascade Cash-Flow
                st.markdown("#### Cascade du Cash-flow")
                # Sélecteur d'année
                years_available = len(results_data.get('monthly_data', pd.DataFrame()).resample('YE').count().index)
                if years_available > 0:
                    year_index = st.slider("Sélectionner l'année pour la cascade", 1, years_available, 5) - 1
                    fig_waterfall = self.create_waterfall_cashflow_chart(results_data, year_index)
                    if fig_waterfall:
                        st.plotly_chart(fig_waterfall, use_container_width=True)
                    else:
                        st.warning("Impossible de générer le graphique cascade.")
            
            with revenus_tab:
                # Répartition Annuelle des Revenus
                fig_revenue_breakdown = self.create_annual_revenue_breakdown_chart(results_data)
                if fig_revenue_breakdown:
                    st.plotly_chart(fig_revenue_breakdown, use_container_width=True)
                else:
                    st.warning("Impossible de générer le graphique de répartition des revenus.")
            
            with dette_tab:
                # Évolution du Solde de la Dette
                fig_debt = self.create_debt_balance_chart(results_data)
                if fig_debt:
                    st.plotly_chart(fig_debt, use_container_width=True)
                else:
                    st.warning("Données de dette insuffisantes ou colonne 'Solde_Dette_Fin_Mois' manquante.")
            
            with profils_tab:
                st.markdown("#### Profil Journalier Moyen (Agrégé)")
                st.caption("Ce graphique compare la production et la consommation moyennes heure par heure sur une journée type.")
                # Appel de la fonction qui retourne fig ET suggestions
                fig, specific_suggestions = self.create_daily_pattern_chart(results=results_data)

                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                    # Afficher les suggestions spécifiques retournées par la fonction
                    if specific_suggestions:
                        st.markdown("---")
                        st.subheader("📊 Analyse du Profil et Suggestions :")
                        for suggestion_text in specific_suggestions:
                            # Utiliser markdown pour interpréter les icônes et le gras
                            st.markdown(f"* {suggestion_text}")
                # Le cas d'erreur est géré dans la fonction create_... elle-même par st.warning/st.error

            with mc_tab:
                if mc_results and isinstance(mc_results, dict) and 'statistics' in mc_results:
                    fig_mc = self.create_monte_carlo_results_chart(mc_results)
                    if fig_mc:
                        st.plotly_chart(fig_mc, use_container_width=True)
                        
                    # Ajout des box plots pour compléter
                    fig_boxplot = self.create_monte_carlo_boxplot(mc_results)
                    if fig_boxplot:
                        st.plotly_chart(fig_boxplot, use_container_width=True)
                else:
                    st.info("Aucun résultat Monte Carlo disponible pour ce scénario. Lancez d'abord la simulation Monte Carlo dans l'onglet 'Analyse & Optimisation'.")