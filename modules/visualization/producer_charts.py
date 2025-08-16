import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px # Pour create_debt_balance_chart

# Fonctions copiées et potentiellement adaptées de votre visualization.py original

def create_financial_indicators_chart(results):
    """
    Crée un graphique des indicateurs financiers annuels.
    """
    if not results or not isinstance(results, dict) or 'monthly_data' not in results:
        st.warning("Données financières invalides pour graphique indicateurs.")
        return None
    
    monthly_df = results.get('monthly_data')
    if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty:
        st.warning("DataFrame mensuel vide pour graphique indicateurs.")
        return None
    
    try:
        df_agg = monthly_df.copy()
        if not isinstance(df_agg.index, pd.DatetimeIndex):
             try: df_agg.index = pd.to_datetime(df_agg.index)
             except: st.error("Index non Datetime pour graphique indicateurs."); return None
                 
        annual_data = df_agg.resample('Y').sum()
        annual_data['Year'] = annual_data.index.year
        
        required_cols = ['Revenus_Total', 'OPEX', 'EBITDA', 'Service_Dette'] # Simplifié, FCFE et Impots peuvent être complexes
        # Tentative de calcul FCFE si manquant
        if 'FCFE' not in annual_data.columns and all(c in annual_data for c in ['Resultat_Net', 'Amortissement', 'Principal_Rembourse']):
            annual_data['FCFE'] = annual_data['Resultat_Net'] + annual_data['Amortissement'] - annual_data['Principal_Rembourse']
        
        if 'FCFE' in annual_data.columns:
             annual_data['Cumulative_FCFE'] = annual_data['FCFE'].cumsum()
        else: annual_data['Cumulative_FCFE'] = 0
        
        if 'Tax_Payment' in annual_data.columns and 'EBITDA' in annual_data.columns: # Tax_Payment au lieu de Impots_Provisionnes
            annual_data['CADS'] = annual_data['EBITDA'] - annual_data['Tax_Payment']
        elif 'EBITDA' in annual_data.columns:
            st.info("Colonne 'Tax_Payment' non trouvée pour DSCR annuel, CADS = EBITDA.")
            annual_data['CADS'] = annual_data['EBITDA']
        else:
            annual_data['CADS'] = 0


        if 'Service_Dette' in annual_data.columns:
            annual_data['DSCR_Calculated'] = np.where(
                np.abs(annual_data['Service_Dette']) > 1e-9,
                annual_data['CADS'] / annual_data['Service_Dette'], np.inf
            )
            annual_data.loc[(annual_data['CADS'] <= 0) & (np.abs(annual_data['Service_Dette']) <= 1e-9), 'DSCR_Calculated'] = np.nan
        else:
            annual_data['DSCR_Calculated'] = np.nan
                 
    except Exception as e_agg:
        st.error(f"Erreur agrégation annuelle pour graphique indicateurs: {e_agg}")
        return None
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.15,
                        subplot_titles=("Flux Financiers Annuels", "DSCR Annuel"))
    
    if 'Revenus_Total' in annual_data:
        fig.add_trace(go.Bar(x=annual_data['Year'], y=annual_data['Revenus_Total'], name='Revenus', marker_color='#2ca02c'), row=1, col=1)
    if 'OPEX' in annual_data:
        fig.add_trace(go.Bar(x=annual_data['Year'], y=annual_data['OPEX'], name='OPEX', marker_color='#ff7f0e'), row=1, col=1)
    if 'FCFE' in annual_data:
        fig.add_trace(go.Scatter(x=annual_data['Year'], y=annual_data['FCFE'], name='FCFE', mode='lines+markers', line=dict(color='#9467bd'), marker=dict(symbol='circle')), row=1, col=1)
    if 'Cumulative_FCFE' in annual_data:
        fig.add_trace(go.Scatter(x=annual_data['Year'], y=annual_data['Cumulative_FCFE'], name='FCFE Cumulé', mode='lines+markers', line=dict(color='#d62728'), marker=dict(symbol='diamond')), row=1, col=1)
    
    if 'DSCR_Calculated' in annual_data and annual_data['DSCR_Calculated'].notna().any():
        fig.add_trace(go.Scatter(x=annual_data['Year'], y=annual_data['DSCR_Calculated'], name='DSCR', mode='lines+markers', line=dict(color='#17becf')), row=2, col=1)
        target_dscr = st.session_state.config.get('target_dscr', 1.2)
        fig.add_shape(type="line", layer='below',
                      x0=annual_data['Year'].min(), y0=target_dscr,
                      x1=annual_data['Year'].max(), y1=target_dscr,
                      line=dict(color="#ff7f0e", width=2, dash="dash"), row=2, col=1)
        fig.add_annotation(x=annual_data['Year'].max(), y=target_dscr, text=f"Cible DSCR: {target_dscr}",
                           showarrow=False, yshift=10, xanchor='right', font=dict(color="#ff7f0e"), row=2, col=1)
    
    fig.update_layout(height=650, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), barmode='relative')
    fig.update_yaxes(title_text="Montant (€)", row=1, col=1)
    dscr_max_val = 2.5
    if 'DSCR_Calculated' in annual_data and annual_data['DSCR_Calculated'].notna().any():
        finite_dscr = annual_data['DSCR_Calculated'][np.isfinite(annual_data['DSCR_Calculated'])]
        if not finite_dscr.empty:
            dscr_max_val = max(2.5, finite_dscr.max() * 1.1)
    fig.update_yaxes(title_text="DSCR", range=[0, dscr_max_val], row=2, col=1)
    fig.update_xaxes(title_text="Année", row=2, col=1)
    return fig

def create_waterfall_cashflow_chart(results, year_index=4):
    """
    Crée un graphique en cascade pour une année spécifique.
    """
    if not results or 'monthly_data' not in results: return None
    monthly_df = results.get('monthly_data')
    if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty: return None
    
    try:
        df_agg = monthly_df.copy()
        if not isinstance(df_agg.index, pd.DatetimeIndex):
            try: df_agg.index = pd.to_datetime(df_agg.index)
            except: return None
    
        annual_data = df_agg.resample('Y').sum()
        years = annual_data.index.year.tolist()
        if not years: return None
        year_index = min(year_index, len(years) - 1) # S'assurer que l'index est valide
        
        year_data = annual_data.iloc[year_index]
        selected_year = years[year_index]
        
        annual_tax_payment = year_data.get('Tax_Payment', 0.0) # Utiliser Tax_Payment

        components = []
        values = []
        
        if 'Revenus_Autoconsommation' in year_data:
            components.append("Revenus Autoconsommation")
            values.append(year_data['Revenus_Autoconsommation'])
        if 'Revenus_Surplus' in year_data:
            components.append("Revenus Surplus")
            values.append(year_data['Revenus_Surplus'])
        if 'OPEX' in year_data:
            components.append("OPEX")
            values.append(-year_data['OPEX'])
        if 'Service_Dette' in year_data and abs(year_data['Service_Dette']) > 1e-6:
            components.append("Service de la Dette")
            values.append(-year_data['Service_Dette'])
        
        # Utiliser la variable annual_tax_payment calculée
        components.append("Impôts Payés") # Changement de libellé pour refléter Tax_Payment
        values.append(-annual_tax_payment) 
        
        components.append("Cash-flow Net Annuel") # Libellé plus précis
            
        fig = go.Figure(go.Waterfall(
            name=f"Cascade Cash-flow Année {selected_year}", orientation="v",
            measure=["relative"] * (len(components) - 1) + ["total"],
            x=components, textposition="outside",
            text=[f"{v:,.0f}€" for v in values[:-1]] + [""], # Formatter le texte
            y=values, connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "#FF4136"}},
            increasing={"marker": {"color": "#3D9970"}},
            totals={"marker": {"color": "#1E88E5"}}
        ))
        fig.update_layout(title=f"Cascade du Cash-flow - Année {selected_year}",
                          showlegend=False, height=500,
                          xaxis_title="Composantes du Cash-flow Annuel", yaxis_title="Montant (€)",
                          yaxis=dict(tickformat=",.0f €")) # Formatage €
    except Exception as e:
        st.error(f"Erreur création graphique cascade: {e}")
        return None
    return fig

def create_debt_balance_chart(results):
    """Crée un graphique de l'évolution du solde de la dette."""
    if not results or 'monthly_data' not in results: return None
    monthly_df = results.get('monthly_data')
    if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty or 'Solde_Dette_Fin_Mois' not in monthly_df.columns:
        return None

    df_chart = monthly_df.copy()
    if not isinstance(df_chart.index, pd.DatetimeIndex):
        if 'Temps' in df_chart.columns: # Assumer que 'Temps' peut être converti
             try: df_chart.index = pd.to_datetime(df_chart['Temps'])
             except: return None # Échec conversion
        else: # Essayer de convertir l'index existant
             try: df_chart.index = pd.to_datetime(df_chart.index)
             except: return None

    fig = px.line(
        df_chart, y='Solde_Dette_Fin_Mois',
        title="Évolution du Solde de la Dette Restante",
        labels={'index': 'Date', 'Solde_Dette_Fin_Mois': 'Solde Restant Dû (€)'}
    )
    fig.update_layout(yaxis_tickformat=",.0f")
    return fig

def create_annual_revenue_breakdown_chart(results):
    """Crée un graphique en barres empilées de la répartition annuelle des revenus."""
    if not results or 'monthly_data' not in results: return None
    monthly_df = results.get('monthly_data')
    if not isinstance(monthly_df, pd.DataFrame) or monthly_df.empty: return None
    
    required_cols = ['Revenus_Autoconsommation', 'Revenus_Surplus', 'Prime_Autoconso_Encaissee']
    # Vérifier et renommer si des noms alternatifs sont utilisés
    monthly_df_agg = monthly_df.copy()
    # (Logique de renommage/vérification des colonnes à ajouter si nécessaire, similaire à create_energy_distribution_pie)

    if not all(col in monthly_df_agg.columns for col in required_cols):
        missing_cols = [col for col in required_cols if col not in monthly_df_agg.columns]
        st.warning(f"Colonnes manquantes pour la répartition des revenus: {missing_cols}")
        # Si Prime_Autoconso_Encaissee manque, on peut continuer sans, ou la mettre à 0
        if 'Prime_Autoconso_Encaissee' not in monthly_df_agg.columns:
            monthly_df_agg['Prime_Autoconso_Encaissee'] = 0.0
            required_cols.remove('Prime_Autoconso_Encaissee') # Enlever des requis si on la met à 0
            if not all(col in monthly_df_agg.columns for col in ['Revenus_Autoconsommation', 'Revenus_Surplus']):
                return None # Si les autres revenus manquent aussi, on ne peut pas continuer

    if not isinstance(monthly_df_agg.index, pd.DatetimeIndex):
        try: monthly_df_agg.index = pd.to_datetime(monthly_df_agg.index)
        except: return None
    
    annual_revenues = monthly_df_agg[required_cols].resample('Y').sum()
    annual_revenues.index = annual_revenues.index.year

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=annual_revenues.index, y=annual_revenues['Revenus_Autoconsommation'],
        name='Revenus Autoconsommation', marker_color='rgb(31, 119, 180)'
    ))
    fig.add_trace(go.Bar(
        x=annual_revenues.index, y=annual_revenues['Revenus_Surplus'],
        name='Revenus Surplus (OA)', marker_color='rgb(255, 127, 14)'
    ))
    if 'Prime_Autoconso_Encaissee' in annual_revenues.columns: # Ajouter la prime si elle existe
        fig.add_trace(go.Bar(
            x=annual_revenues.index, y=annual_revenues['Prime_Autoconso_Encaissee'],
            name='Prime Autoconsommation', marker_color='rgb(44, 160, 44)' # Vert
        ))
    fig.update_layout(
        barmode='stack', title="Répartition Annuelle des Revenus",
        xaxis_title="Année", yaxis_title="Revenus Annuels (€)",
        legend_title="Source de Revenus", yaxis_tickformat=",.0f"
    )
    return fig


def create_daily_pattern_chart(results: dict | None) -> tuple[go.Figure | None, list[str] | None]:
    """
    Crée le graphique des profils journaliers moyens ET génère des suggestions.
    """
    suggestions = []
    fig = None
    if not results or 'hourly_aggregated_data' not in results:
        st.info("Données horaires agrégées non trouvées pour profil journalier.")
        return None, None
    df_hourly = results.get('hourly_aggregated_data')
    if not isinstance(df_hourly, pd.DataFrame) or df_hourly.empty:
        st.warning("DataFrame horaire vide pour profil journalier.")
        return None, None

    df = df_hourly.copy()
    required_cols = ['production_kwh', 'consumption_kwh']
    
    # S'assurer que l'index est Datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        if 'Temps' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['Temps']):
                try: df['Temps'] = pd.to_datetime(df['Temps'], errors='coerce')
                except: st.error("Conversion 'Temps' échouée pour profil journalier."); return None, None
            df = df.dropna(subset=['Temps']).set_index('Temps')
        else: st.error("Index non Datetime et 'Temps' manquant pour profil journalier."); return None, None
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols: st.error(f"Colonnes manquantes pour profil journalier: {missing_cols}"); return None, None

    try:
        for col in required_cols + ['autoconsumption_kwh', 'surplus_kwh']:
             if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                  try: df[col] = pd.to_numeric(df[col], errors='coerce')
                  except: df[col] = 0.0
        df = df.fillna(0.0)

        df['hour'] = df.index.hour
        if 'autoconsumption_kwh' not in df.columns:
             df['autoconsumption_kwh'] = np.minimum(df['production_kwh'], df['consumption_kwh'])
        if 'surplus_kwh' not in df.columns:
             df['surplus_kwh'] = (df['production_kwh'] - df['autoconsumption_kwh']).clip(lower=0)

        hourly_means = df.groupby('hour')[['production_kwh', 'consumption_kwh', 'autoconsumption_kwh', 'surplus_kwh']].mean()
        if len(hourly_means) < 24:
             hourly_means = hourly_means.reindex(range(24), fill_value=0.0)

        heures_solaires = range(9, 17); heures_pic_soir = range(18, 22); heures_pic_matin = range(6, 9)
        hourly_means['net_power'] = hourly_means['production_kwh'] - hourly_means['consumption_kwh']
        max_surplus_jour = hourly_means.loc[hourly_means.index.isin(heures_solaires), 'net_power'].clip(lower=0).max()
        avg_prod_jour = hourly_means.loc[hourly_means.index.isin(heures_solaires), 'production_kwh'].mean()
        max_deficit_soir_matin = abs(hourly_means.loc[hourly_means.index.isin(list(heures_pic_soir) + list(heures_pic_matin)), 'net_power'].clip(upper=0).min())
        avg_conso_pics = hourly_means.loc[hourly_means.index.isin(list(heures_pic_soir) + list(heures_pic_matin)), 'consumption_kwh'].mean()
        seuil_surplus_relatif = 0.20; seuil_deficit_relatif = 0.30
        surplus_significatif = max_surplus_jour > (avg_prod_jour * seuil_surplus_relatif) if avg_prod_jour > 1e-3 else False
        deficit_significatif = max_deficit_soir_matin > (avg_conso_pics * seuil_deficit_relatif) if avg_conso_pics > 1e-3 else False

        suggestions.append("💡 **Analysez les Courbes :** Observez les moments où la production (jaune/or) dépasse la consommation (bleue) et vice-versa.")
        if surplus_significatif: suggestions.append(f"☀️ **Fort Surplus Détecté :** Un surplus moyen important (max ~{max_surplus_jour:.1f} kWh/h) est produit en journée. **Priorité : Stockage batterie ou pilotage de charges**.")
        else: suggestions.append("✔️ **Surplus Journalier Limité :** Le surplus en journée semble modéré. L'impact du stockage/pilotage pourrait être moins important.")
        if deficit_significatif: suggestions.append(f"🌙 **Fort Déficit Détecté :** Un besoin important depuis le réseau (max ~{max_deficit_soir_matin:.1f} kWh/h) apparaît le matin/soir. Stockage ou décalage de consommations serait utile.")
        else: suggestions.append("✔️ **Déficit Matin/Soir Limité :** Les pointes de consommation matin/soir semblent modérées.")
        if surplus_significatif or deficit_significatif: suggestions.append("👥 **Mix Consommateurs :** Envisager des profils de consommation complémentaires aiderait à équilibrer les flux.")

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
        return fig, suggestions
    except Exception as e:
        st.error(f"Erreur création profil journalier : {e}")
        return None, None

def create_monte_carlo_results_chart(mc_results):
    """
    Crée un graphique des résultats de la simulation Monte Carlo.
    """
    if not mc_results or not isinstance(mc_results, dict) or \
       'probabilities' not in mc_results or \
       'results' not in mc_results or \
       'statistics' not in mc_results: # Changé de 'results_all_iterations' à 'results'
        st.warning("Données MC invalides pour graphique.")
        return None
    
    raw_values_mc = mc_results.get('results', {}) # Devrait être 'results' selon votre logique_optimisation
    stats_mc = mc_results.get('statistics', {})
    contraintes_mc = mc_results.get('contraintes_mc_cibles_appliquees', mc_results.get('contraintes_mc', {})) # Gérer les deux clés
    scenario_name_mc = mc_results.get('scenario_name', 'Inconnu')
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Distribution VAN Equity (€)", "Distribution TRI Equity (%)", 
                        "Distribution Payback Equity (ans)", "Distribution DSCR Moyen"),
        vertical_spacing=0.15, horizontal_spacing=0.1
    )
    
    metrics_mc_plot = [
        {'key': 'npv', 'name': 'VAN Equity (€)', 'unit': '€', 'multiplier': 1, 'row': 1, 'col': 1, 'color': '#1f77b4', 'target_key': None}, # VAN cible souvent 0
        {'key': 'irr', 'name': 'TRI Equity (%)', 'unit': '%', 'multiplier': 100, 'row': 1, 'col': 2, 'color': '#2ca02c', 'target_key': 'cout_fonds_propres'},
        {'key': 'payback_period', 'name': 'Payback Equity (ans)', 'unit': 'ans', 'multiplier': 1, 'row': 2, 'col': 1, 'color': '#ff7f0e', 'target_key': 'payback_max_equity_annees'},
        {'key': 'avg_dscr', 'name': 'DSCR Moyen', 'unit': None, 'multiplier': 1, 'row': 2, 'col': 2, 'color': '#d62728', 'target_key': 'dscr_moyen_min'}
    ] # J'ai utilisé dscr_moyen_min car c'est ce que vous avez dans la config MC
    
    for metric in metrics_mc_plot:
        metric_key_mc = metric['key']
        # 'results' dans mc_results contient déjà les listes de valeurs par clé (ex: npv_values)
        # donc raw_values_mc[f"{metric_key_mc}_values"] devrait fonctionner
        values_key_mc = f"{metric_key_mc}_values" 
        
        if values_key_mc not in raw_values_mc or metric_key_mc not in stats_mc:
            print(f"WARN MC Plot: Données manquantes pour {metric_key_mc}")
            continue
             
        data_values_mc = np.array(raw_values_mc[values_key_mc])
        data_values_mc = data_values_mc[np.isfinite(data_values_mc)]
        stat_info_mc = stats_mc[metric_key_mc]
        mean_val_mc = stat_info_mc.get('mean', np.nan)
        
        target_val_mc = None
        if metric.get('target_key'):
            # Pourrait être dans st.session_state.config ou dans contraintes_mc
            target_val_mc = contraintes_mc.get(metric['target_key'], st.session_state.config.get(metric['target_key']))


        fig.add_trace(go.Histogram(x=data_values_mc * metric['multiplier'], name=metric['name'],
                                   marker_color=metric['color'], opacity=0.75, nbinsx=30),
                      row=metric['row'], col=metric['col'])
        
        if pd.notna(mean_val_mc):
             mean_plot_mc = mean_val_mc * metric['multiplier']
             fig.add_vline(x=mean_plot_mc, line_width=2, line_dash="dash", line_color="#8c564b",
                           annotation_text=f"Moy: {mean_plot_mc:.2f}{metric.get('unit','')}", 
                           annotation_position="top right", row=metric['row'], col=metric['col'])
        
        if target_val_mc is not None and pd.notna(target_val_mc):
            # Le target pour cout_fonds_propres est en % (ex: 8.0), pas besoin de multiplier par 100 si metric['multiplier'] est déjà 100
            target_plot_mc = target_val_mc * metric['multiplier'] if metric_key_mc != 'irr' else target_val_mc
            
            color_cible_mc = "#2ca02c" 
            if metric_key_mc == 'payback_period': color_cible_mc = "#d62728"
            fig.add_vline(x=target_plot_mc, line_width=2, line_dash="dot", line_color=color_cible_mc,
                          annotation_text=f"Cible: {target_plot_mc:.2f}{metric.get('unit','')}", 
                          annotation_position="bottom right", row=metric['row'], col=metric['col'])
                          
        fig.update_xaxes(title_text=metric['name'], row=metric['row'], col=metric['col'])
        fig.update_yaxes(title_text="Fréquence", row=metric['row'], col=metric['col'])

    fig.update_layout(title_text=f"Distributions Monte Carlo - Scénario: {scenario_name_mc}",
                      height=700, showlegend=False, bargap=0.1)
    return fig


def create_monte_carlo_boxplot(mc_results):
    """Crée des box plots pour les résultats clés de Monte Carlo."""
    if not mc_results or 'results' not in mc_results or 'statistics' not in mc_results: # Changé results_all_iterations
         return None

    data_mc_box = mc_results.get('results', {}) # Changé results_all_iterations
    # stats_mc_box = mc_results.get('statistics', {}) # Pas utilisé directement ici
    metrics_mc_box_plot = {
        'npv': {'name': 'VAN Equity (€)', 'data_key': 'npv_values'},
        'irr': {'name': 'TRI Equity (%)', 'data_key': 'irr_values', 'multiplier': 100},
        'payback_period': {'name': 'Payback Equity (ans)', 'data_key': 'payback_period_values'},
        'avg_dscr': {'name': 'DSCR Moyen', 'data_key': 'avg_dscr_values'}
    }

    fig = go.Figure()
    for key_box, info_box in metrics_mc_box_plot.items():
        values_box = data_mc_box.get(info_box['data_key'])
        if values_box is not None:
            valid_values_box = np.array(values_box)
            valid_values_box = valid_values_box[np.isfinite(valid_values_box)]
            if len(valid_values_box) > 0:
                multiplier_box = info_box.get('multiplier', 1)
                fig.add_trace(go.Box(y=valid_values_box * multiplier_box, name=info_box['name'],
                                     boxpoints='outliers', jitter=0.3, pointpos=-1.8))
    fig.update_layout(title="Distribution des Résultats Clés (Monte Carlo - Box Plots)",
                      yaxis_title="Valeur", showlegend=True) # showlegend=True pour voir les noms
    return fig

# Les fonctions create_sensitivity_tornado_chart et display_sensitivity_analysis
# peuvent rester ici si vous les utilisez pour l'analyse producteur,
# ou être déplacées dans un fichier dédié (ex: sensitivity_charts.py)
# Pour l'instant, je les laisse ici par simplicité, car elles étaient dans le visualization.py original.

def create_sensitivity_tornado_chart(base_result, sensitivity_results):
    """
    Crée un graphique Tornado montrant l'impact des variations des paramètres.
    """
    # ... (code existant de la fonction, semble correct) ...
    if not base_result or not sensitivity_results: return None
    if 'npv' not in base_result or 'irr' not in base_result: return None
    base_npv = base_result.get('npv', 0); base_irr = base_result.get('irr', 0) * 100
    tornado_data = []
    for param, results_sens in sensitivity_results.items():
        param_values = []; npv_deltas = []; irr_deltas = []
        for value, result_sens in results_sens.items():
            if 'npv' in result_sens and 'irr' in result_sens:
                param_values.append(value)
                npv_deltas.append(result_sens['npv'] - base_npv)
                irr_deltas.append(result_sens['irr'] * 100 - base_irr)
        if param_values:
            tornado_data.append({'parameter': param, 'min_npv_delta': min(npv_deltas),
                                 'max_npv_delta': max(npv_deltas), 'min_irr_delta': min(irr_deltas),
                                 'max_irr_delta': max(irr_deltas)})
    if not tornado_data: return None
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Impact sur la VAN (€)", "Impact sur le TRI (%)"), horizontal_spacing=0.1)
    tornado_data.sort(key=lambda x: abs(x['max_npv_delta'] - x['min_npv_delta']), reverse=True)
    parameters = [item['parameter'] for item in tornado_data]
    fig.add_trace(go.Bar(y=parameters, x=[item['min_npv_delta'] for item in tornado_data], orientation='h', name='Impact Négatif VAN', marker=dict(color='rgba(255, 65, 54, 0.7)'), showlegend=True), row=1, col=1)
    fig.add_trace(go.Bar(y=parameters, x=[item['max_npv_delta'] for item in tornado_data], orientation='h', name='Impact Positif VAN', marker=dict(color='rgba(61, 153, 112, 0.7)'), showlegend=True), row=1, col=1)
    fig.add_trace(go.Bar(y=parameters, x=[item['min_irr_delta'] for item in tornado_data], orientation='h', name='Impact Négatif TRI', marker=dict(color='rgba(255, 65, 54, 0.7)'), showlegend=False), row=1, col=2)
    fig.add_trace(go.Bar(y=parameters, x=[item['max_irr_delta'] for item in tornado_data], orientation='h', name='Impact Positif TRI', marker=dict(color='rgba(61, 153, 112, 0.7)'), showlegend=False), row=1, col=2)
    fig.update_layout(barmode='relative', height=500, title="Analyse de Sensibilité (Tornado)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_xaxes(title_text="Variation VAN (€)", row=1, col=1); fig.update_xaxes(title_text="Variation TRI (%)", row=1, col=2)
    fig.update_yaxes(title_text="Paramètre", row=1, col=1); fig.update_yaxes(title_text="", row=1, col=2)
    return fig

def display_sensitivity_analysis_section(selected_scenario): # Modifié pour être une fonction autonome
    """ Affiche la section d'analyse de sensibilité pour le scénario sélectionné. """
    # ... (code existant de la fonction, semble correct) ...
    # Note: cette fonction appelle create_sensitivity_tornado_chart
    # Elle devrait probablement être dans un module UI ou appelée par la show_ui principale.
    # Pour l'instant, on la garde ici pour la cohérence avec votre structure originale.
    if 'constrained_optim_results' not in st.session_state or \
       selected_scenario not in st.session_state.constrained_optim_results:
        st.warning(f"Résultats d'optimisation non trouvés pour le scénario {selected_scenario}.")
        return

    optim_results_base = st.session_state.constrained_optim_results[selected_scenario]
    base_results = optim_results_base.get('indicateurs_au_prix_optimal')
    if not base_results or 'monthly_data' not in base_results: 
        st.error(f"Indicateurs manquants pour scénario de base {selected_scenario}."); return
    
    # Note: La logique de comparaison avec d'autres scénarios (results_sensitivity)
    # n'est pas implémentée dans le code fourni de visualization.py.
    # On va donc se concentrer sur l'idée de présenter la sensibilité d'UN scénario
    # à ses propres paramètres, ce qui nécessiterait une logique de simulation de sensibilité
    # en amont (par exemple dans logique_optimisation.py).
    # Pour l'instant, on affiche un message si les données de sensibilité ne sont pas là.

    if 'sensitivity_results' in st.session_state and \
       selected_scenario in st.session_state.sensitivity_results:
        
        results_sensitivity = st.session_state.sensitivity_results[selected_scenario]
        
        # Paramètres à afficher (pourrait être configurable par l'utilisateur)
        params_for_tornado = list(results_sensitivity.keys()) # Afficher tous les params testés

        if len(params_for_tornado) > 0: # Modifié pour vérifier s'il y a des paramètres
            tornado_fig = create_sensitivity_tornado_chart(base_results, results_sensitivity)
            if tornado_fig:
                st.plotly_chart(tornado_fig, use_container_width=True)
            else:
                st.warning("Impossible de créer le graphique Tornado de sensibilité.")
        else:
             st.info("Aucun paramètre de sensibilité sélectionné ou disponible pour le graphique Tornado.")
        
        # (Le code pour les graphiques individuels par paramètre peut être ajouté ici si besoin)

    else:
        st.info(f"Aucun résultat d'analyse de sensibilité disponible pour le scénario '{selected_scenario}'.")
        st.caption("Pour effectuer une analyse de sensibilité, vous devez d'abord la calculer (cette fonctionnalité n'est pas encore implémentée dans l'interface principale).")