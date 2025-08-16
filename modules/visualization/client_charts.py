import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Fonctions copiées et potentiellement adaptées de votre visualization.py original

def create_price_comparison_chart(results_data, config):
    """
    Crée un graphique de comparaison entre le prix optimal et le tarif EDF.
    """
    if not results_data or 'prix_revente' not in results_data:
        return None
    
    prix_optimal = results_data.get('prix_revente', 0)
    tarif_edf = config.get('tarif_edf_reference', 0.21)
    
    if tarif_edf > 0:
        economie_pct = ((tarif_edf - prix_optimal) / tarif_edf) * 100
    else:
        economie_pct = 0
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Prix Optimal', 'Tarif EDF'],
        y=[prix_optimal, tarif_edf],
        text=[f"{prix_optimal:.4f} €/kWh", f"{tarif_edf:.4f} €/kWh"],
        textposition='outside',
        marker_color=['#2ca02c', '#d62728'],
        hoverinfo='text',
        hovertext=[f"Prix Optimal: {prix_optimal:.4f} €/kWh", f"Tarif EDF: {tarif_edf:.4f} €/kWh"]
    ))
    fig.add_annotation(
        x=0.5, y=max(prix_optimal, tarif_edf) * 1.15,
        text=f"Économie: {economie_pct:.1f}%", showarrow=False,
        font=dict(size=14, color="#2ca02c" if economie_pct > 0 else "#d62728")
    )
    fig.update_layout(
        title="Comparaison des Prix (€/kWh)", yaxis_title="Prix (€/kWh)",
        showlegend=False, height=400, yaxis=dict(tickformat=",.4f"),
        xaxis=dict(tickangle=-45)
    )
    return fig

def create_annual_savings_chart(results_data, config):
    """
    Calcule et affiche l'économie annuelle estimée pour le client.
    """
    if not results_data or 'monthly_data' not in results_data:
        return None
    
    monthly_data = results_data.get('monthly_data')
    if not isinstance(monthly_data, pd.DataFrame) or monthly_data.empty:
        return None
    
    prix_optimal = results_data.get('prix_revente', 0)
    tarif_edf = config.get('tarif_edf_reference', 0.21)
    
    if 'Autoconsommation_kWh' in monthly_data.columns:
        autoconsommation_annuelle = monthly_data['Autoconsommation_kWh'].sum()
    else:
        return None
    
    economie_kwh = tarif_edf - prix_optimal
    economie_annuelle = economie_kwh * autoconsommation_annuelle
    economie_pct = (economie_kwh / tarif_edf) * 100 if tarif_edf > 0 else 0
    
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode="number+gauge+delta", value=economie_annuelle,
        number={"prefix": "", "suffix": " €", "valueformat": ",.2f"},
        title={"text": "Économie Annuelle (€)"},
        gauge={"axis": {"range": [0, economie_annuelle * 1.5 if economie_annuelle > 0 else 100]},
               "bar": {"color": "#2ca02c"},
               "steps": [{"range": [0, economie_annuelle], "color": "#e8f5e9"}]},
        domain={"row": 0, "column": 0}
    ))
    fig.add_trace(go.Indicator(
        mode="number+gauge+delta", value=economie_pct,
        number={"suffix": " %", "valueformat": ".1f"},
        title={"text": "Économie (%)"},
        gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#2ca02c"},
               "steps": [{"range": [0, economie_pct], "color": "#e8f5e9"}]},
        domain={"row": 0, "column": 1}
    ))
    fig.update_layout(
        grid={"rows": 1, "columns": 2, "pattern": "independent"},
        title="Économies pour le Client", height=250
    )
    return fig

def create_energy_distribution_pie(results_data):
    """
    Crée un graphique camembert de la répartition de l'énergie produite.
    """
    if not results_data or 'monthly_data' not in results_data:
        return None
    
    monthly_data_df = results_data.get('monthly_data')
    if not isinstance(monthly_data_df, pd.DataFrame) or monthly_data_df.empty:
        return None
    
    # Utiliser une copie pour éviter SettingWithCopyWarning
    monthly_data = monthly_data_df.copy()

    required_cols = ['Autoconsommation_kWh', 'Surplus_kWh']
    alt_cols_map = {
        'Autoconsommation_kWh': ['autoconsumption_kwh', 'autoconsommation_kwh'],
        'Surplus_kWh': ['surplus_kwh', 'surplus']
    }
    
    for req_col, alt_names in alt_cols_map.items():
        if req_col not in monthly_data.columns:
            for alt_name in alt_names:
                if alt_name in monthly_data.columns:
                    monthly_data.rename(columns={alt_name: req_col}, inplace=True)
                    break
    
    if not all(col in monthly_data.columns for col in required_cols):
        st.warning(f"Colonnes nécessaires pour le camembert non trouvées: {required_cols}")
        return None
            
    autoconsommation_totale = monthly_data['Autoconsommation_kWh'].sum()
    surplus_total = monthly_data['Surplus_kWh'].sum()
    
    labels = ['Autoconsommation Locale', 'Surplus Injecté']
    values = [autoconsommation_totale, surplus_total]
    colors = ['#2ca02c', '#ff7f0e']
    
    production_totale = autoconsommation_totale + surplus_total
    taux_autoconsommation = (autoconsommation_totale / production_totale * 100) if production_totale > 0 else 0
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, marker=dict(colors=colors),
        textinfo='value+percent', insidetextorientation='radial',
        hoverinfo='label+value+percent', hole=0.4
    )])
    fig.add_annotation(
        text=f"{taux_autoconsommation:.1f}%<br>Autoconsommation",
        x=0.5, y=0.5, font_size=14, showarrow=False
    )
    fig.update_layout(
        title="Répartition de l'Énergie Produite", height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    return fig

def create_facture_comparison_chart(results_data, config):
    """
    Crée un graphique comparant la facture annuelle avec et sans ACOC.
    """
    if not results_data or 'monthly_data' not in results_data:
        return None
    
    monthly_data_df = results_data.get('monthly_data')
    if not isinstance(monthly_data_df, pd.DataFrame) or monthly_data_df.empty:
        return None

    # Utiliser une copie
    monthly_data = monthly_data_df.copy()
    
    prix_optimal = results_data.get('prix_revente', 0)
    tarif_edf = config.get('tarif_edf_reference', 0.21)
    
    required_cols = ['Autoconsommation_kWh', 'Consommation_kWh']
    alt_cols_map = {
        'Autoconsommation_kWh': ['autoconsumption_kwh', 'autoconsommation_kwh'],
        'Consommation_kWh': ['consumption_kwh', 'consommation_kwh']
    }

    for req_col, alt_names in alt_cols_map.items():
        if req_col not in monthly_data.columns:
            for alt_name in alt_names:
                if alt_name in monthly_data.columns:
                    monthly_data.rename(columns={alt_name: req_col}, inplace=True)
                    break
    
    if not all(col in monthly_data.columns for col in required_cols):
        st.warning(f"Colonnes nécessaires pour la comparaison de facture non trouvées: {required_cols}")
        return None

    autoconsommation_annuelle = monthly_data['Autoconsommation_kWh'].sum()
    consommation_annuelle = monthly_data['Consommation_kWh'].sum()
    
    facture_edf = consommation_annuelle * tarif_edf
    facture_autoconso = autoconsommation_annuelle * prix_optimal
    reste_consommation = max(0, consommation_annuelle - autoconsommation_annuelle)
    facture_reste_edf = reste_consommation * tarif_edf
    facture_totale_acoc = facture_autoconso + facture_reste_edf
    
    economie = facture_edf - facture_totale_acoc
    pourcentage_economie = (economie / facture_edf) * 100 if facture_edf > 0 else 0
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Facture Standard EDF'], y=[facture_edf], name='Tarif EDF Standard',
        marker_color='#d62728', text=[f"{facture_edf:.0f} €"], textposition='auto'
    ))
    fig.add_trace(go.Bar(
        x=['Facture avec ACOC'], y=[facture_autoconso], name='Partie Autoconsommation',
        marker_color='#2ca02c', text=[f"{facture_autoconso:.0f} €"], textposition='inside'
    ))
    if reste_consommation > 0:
        fig.add_trace(go.Bar(
            x=['Facture avec ACOC'], y=[facture_reste_edf], name='Partie Restante EDF',
            marker_color='#ff7f0e', text=[f"{facture_reste_edf:.0f} €"], textposition='inside'
        ))
    fig.add_annotation(
        x=0.5, y=max(facture_edf, facture_totale_acoc) * 1.1,
        text=f"Économie: {economie:.0f} € ({pourcentage_economie:.1f}%)",
        showarrow=False, font=dict(size=14, color="#2ca02c")
    )
    fig.update_layout(
        title="Comparaison de Facture Annuelle d'Électricité",
        yaxis_title="Montant Annuel (€)", barmode='stack', showlegend=True, height=450,
        yaxis=dict(tickformat=",.0f €"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    return fig

def create_cumulative_savings_chart(results_data, config):
    """
    Crée un graphique montrant les économies cumulées sur plusieurs années.
    """
    if not results_data or 'monthly_data' not in results_data:
        return None
    
    monthly_data_df = results_data.get('monthly_data')
    if not isinstance(monthly_data_df, pd.DataFrame) or monthly_data_df.empty:
        return None

    monthly_data = monthly_data_df.copy()
    
    prix_vente_scenario = results_data.get('prix_revente') 
    if prix_vente_scenario is None:
         prix_vente_scenario = config.get('prix_vente_initial', 0.15) 
             
    tarif_edf = config.get('tarif_edf_reference', 0.21)
    taux_inflation = config.get('taux_inflation', 2.0) / 100
    
    autoconso_col = None
    if 'Autoconsommation_kWh' in monthly_data.columns:
        autoconso_col = 'Autoconsommation_kWh'
    else:
        alt_cols = ['autoconsumption_kwh', 'autoconsommation_kwh']
        for alt in alt_cols:
            if alt in monthly_data.columns:
                monthly_data.rename(columns={alt: 'Autoconsommation_kWh'}, inplace=True)
                autoconso_col = 'Autoconsommation_kWh'
                break
        else:
            st.warning("Colonne d'autoconsommation non trouvée pour économies cumulées.")
            return None
    
    if not isinstance(monthly_data.index, pd.DatetimeIndex):
        try:
             monthly_data.index = pd.to_datetime(monthly_data.index)
        except Exception:
             st.error("Index non Datetime pour économies cumulées.")
             return None
             
    autoconsommation_par_an = monthly_data[autoconso_col].resample('Y').sum()
    autoconsommation_annuelle_ref = autoconsommation_par_an.mean() if not autoconsommation_par_an.empty else 0
    if autoconsommation_annuelle_ref <= 0:
         st.warning("Volume d'autoconsommation annuel moyen nul ou négatif pour économies cumulées.")
         return None

    duree_projet = config.get('duree_ppa', 240) // 12
    if duree_projet <= 0: duree_projet = 20
    
    annees = list(range(1, duree_projet + 1))
    economies_annuelles = []
    
    for i in range(duree_projet):
        tarif_edf_annee = tarif_edf * (1 + taux_inflation) ** i
        prix_vente_annee = prix_vente_scenario * (1 + taux_inflation) ** i
        economie_kwh_annee = tarif_edf_annee - prix_vente_annee
        economie_annuelle = economie_kwh_annee * autoconsommation_annuelle_ref 
        economies_annuelles.append(economie_annuelle)
    
    economies_cumulees_liste = np.cumsum(economies_annuelles)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=annees, y=economies_annuelles, name="Économie Annuelle",
               marker_color='rgba(44, 160, 44, 0.7)',
               hovertemplate="Année %{x}<br>Économie: %{y:,.0f} €"),
        secondary_y=False
    )
    fig.add_trace(
        go.Scatter(x=annees, y=economies_cumulees_liste, name="Économies Cumulées",
                   line=dict(color='#d62728', width=3), mode='lines+markers',
                   marker=dict(size=6),
                   hovertemplate="Année %{x}<br>Économies Cumulées: %{y:,.0f} €"),
        secondary_y=True
    )
    
    total_savings = 0
    if economies_cumulees_liste.size > 0:
         total_savings = economies_cumulees_liste[-1]
         fig.add_annotation(
             x=duree_projet, y=total_savings, ax=40, ay=-40,
             text=f"Total sur {duree_projet} ans:<br><b>{total_savings:,.0f} €</b>",
             showarrow=True, arrowhead=1, arrowsize=1, arrowwidth=1.5, arrowcolor="#d62728",
             font=dict(size=11, color="#d62728"), bordercolor="#d62728",
             borderwidth=1, bgcolor="rgba(255,255,255,0.7)", align="left",
             secondary_y="y2"
         )
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
                     range=[0, total_savings * 1.1 if economies_cumulees_liste.size > 0 and total_savings > 0 else None])
    return fig