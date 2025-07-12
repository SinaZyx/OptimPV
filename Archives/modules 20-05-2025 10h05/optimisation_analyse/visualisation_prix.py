# modules/optimisation_analyse/visualisation_prix.py

import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_price_benefit_figure(df_data: pd.DataFrame, 
                                cout_prod_ht: float,       # LCOE ou coût de production HT
                                prix_edf_ref_ttc: float,   # Tarif EDF de référence du client TTC
                                selected_price_ht: float | None = None, 
                                optimal_price_ht: float | None = None,
                                taux_tva: float = 0.20) -> go.Figure: # Taux de TVA pour calcul TTC
    """
    Crée la figure Plotly interactive Prix Vente HT vs Bénéfice Client Annuel TTC.
    Affiche le prix TTC dans l'infobulle.
    L'axe X représente le prix de vente HT proposé.
    L'axe Y représente le bénéfice client annuel calculé par rapport au tarif EDF TTC.
    """
    required_cols = ['PrixVenteHT', 'BeneficeClient', 'PctEconomie']
    if not isinstance(df_data, pd.DataFrame) or df_data.empty or not all(c in df_data.columns for c in required_cols):
        missing = [c for c in required_cols if c not in df_data.columns] if isinstance(df_data, pd.DataFrame) else required_cols
        print(f"ERREUR VISU: df_data invalide ou colonnes manquantes: {missing}.")
        return go.Figure(layout=go.Layout(title="Données insuffisantes pour le graphique Prix/Bénéfice"))

    fig = go.Figure()

    # Préparer les données pour l'infobulle (hover)
    df_data_graph = df_data.copy()
    # Le prix de vente TTC pour l'affichage dans l'infobulle
    df_data_graph['PrixVenteTTC_hover'] = df_data_graph['PrixVenteHT'] * (1 + taux_tva)

    fig.add_trace(go.Scatter(
        x=df_data_graph['PrixVenteHT'],      # Axe X: Prix de Vente HT
        y=df_data_graph['BeneficeClient'], # Axe Y: Bénéfice Client (déjà calculé TTC vs TTC)
        mode='lines',
        name='Bénéfice Client Annuel (vs EDF TTC)',
        line=dict(color='#63C5DA', width=3),
        customdata=df_data_graph[['PctEconomie', 'PrixVenteTTC_hover']], # PctEconomie est TTC, PrixVenteTTC_hover est TTC
        hovertemplate=(
            "<b>Prix Vente HT: %{x:.4f} €/kWh</b><br>" +
            "Prix Vente TTC équivalent: %{customdata[1]:.4f} €/kWh<br>" +
            "Bénéfice Client Annuel: %{y:,.0f} €<br>" +
            "Économie Client (vs EDF TTC): %{customdata[0]:.1f}%" +
            "<extra></extra>"
        )
    ))

    # Ligne verticale pour le coût de production (LCOE HT)
    fig.add_vline(x=cout_prod_ht, line_width=2, line_dash="dash", line_color="#FFA07A",
                  annotation_text=f"LCOE (HT): {cout_prod_ht:.4f}€", 
                  annotation_position="bottom right", # Ajusté pour meilleure lisibilité
                  annotation_font_color="#FFA07A")
    
    # Ligne horizontale pour Bénéfice Client = 0
    fig.add_hline(y=0, line_width=1, line_dash="dot", line_color="grey")

    # Annotation pour le tarif EDF de référence TTC (pas une ligne car l'axe X est HT)
    fig.add_annotation(
        text=f"Tarif EDF Réf. (Client): {prix_edf_ref_ttc:.4f} €/kWh TTC",
        align='left', xref="paper", yref="paper", x=0.02, y=0.98, # Position en haut à gauche
        showarrow=False, font=dict(color="#E9967A", size=11),
        bgcolor="rgba(255,250,240,0.7)", bordercolor="#E9967A", borderwidth=1
    )

    # Marqueur pour le prix HT sélectionné par le slider
    if selected_price_ht is not None:
        try:
            # Interpole le bénéfice TTC correspondant au prix HT sélectionné
            interpolated_benefit_ttc = np.interp(selected_price_ht, df_data_graph['PrixVenteHT'], df_data_graph['BeneficeClient'])
            fig.add_trace(go.Scatter(
                x=[selected_price_ht], y=[interpolated_benefit_ttc], mode='markers',
                marker=dict(color='#FF6347', size=12, symbol='star'), 
                name=f'Prix HT Sélectionné ({selected_price_ht:.4f}€)'
            ))
        except Exception as e_interp_sel:
             print(f"AVERTISSEMENT VISU: Interpolation marqueur sélectionné: {e_interp_sel}")

    # Marqueur pour le prix HT optimal
    if optimal_price_ht is not None:
         is_different_from_selected = True
         if selected_price_ht is not None: 
             is_different_from_selected = abs(optimal_price_ht - selected_price_ht) > 1e-5 
              
         if is_different_from_selected: # Éviter superposition exacte
            try:
                optimal_benefit_ttc = np.interp(optimal_price_ht, df_data_graph['PrixVenteHT'], df_data_graph['BeneficeClient'])
                optimal_price_ttc_hover = optimal_price_ht * (1 + taux_tva)
                fig.add_trace(go.Scatter(
                    x=[optimal_price_ht], y=[optimal_benefit_ttc], mode='markers',
                    marker=dict(color='#32CD32', size=10, symbol='diamond'), 
                    name=f'Prix HT Optimal ({optimal_price_ht:.4f}€)',
                    customdata=np.array([[optimal_price_ttc_hover]]), # Pour l'infobulle du marqueur
                    hovertemplate=(
                        "<b>Prix Optimal HT: %{x:.4f} €/kWh</b><br>" +
                        "Prix Optimal TTC équivalent: %{customdata[0]:.4f} €/kWh<br>" +
                        "Bénéfice Client Annuel: %{y:,.0f} €" +
                        "<extra></extra>"
                    )
                ))
                fig.add_annotation(
                    x=optimal_price_ht, y=optimal_benefit_ttc,
                    text=f"Optimal HT: {optimal_price_ht:.4f}€", showarrow=True, arrowhead=1,
                    font=dict(color="#32CD32", size=11), align="left", yshift=10
                )
            except Exception as e_interp_opt:
                print(f"AVERTISSEMENT VISU: Interpolation marqueur optimal: {e_interp_opt}")

    fig.update_layout(
        title_text="Impact du Prix de Vente HT sur le Bénéfice Client Annuel TTC",
        xaxis_title="Prix de Vente Proposé (HT) (€/kWh)",
        yaxis_title="Bénéfice Client Annuel (vs Tarif EDF TTC) (€)",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(tickformat=".4f"), 
        yaxis=dict(tickformat=",.0f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_autoconsommation_surplus_pie_chart(total_autoconsommation: float, total_surplus: float) -> go.Figure:
    """
    Crée un diagramme camembert montrant la répartition entre
    l'autoconsommation et le surplus.
    Args:
        total_autoconsommation: Quantité totale d'énergie autoconsommée (kWh).
        total_surplus: Quantité totale d'énergie en surplus (kWh).

    Returns:
        go.Figure: L'objet figure Plotly prêt à être affiché.
    """
    labels = ['Autoconsommation', 'Surplus']
    values = [total_autoconsommation, total_surplus]
    colors = ['#FFD700', '#1f77b4'] # Or et Bleu Plotly standard

    # Vérification pour éviter les erreurs avec des données nulles ou négatives
    if total_autoconsommation < 0 or total_surplus < 0 or (total_autoconsommation + total_surplus) <= 1e-6: # Tolérance pour flottants
        fig = go.Figure()
        fig.update_layout(
            title="Répartition Autoconsommation / Surplus",
            xaxis = {"visible": False},
            yaxis = {"visible": False},
            annotations=[
                {
                    "text": "Données insuffisantes ou invalides pour afficher le graphique.",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 14
                    }
                }
            ]
        )
        return fig

    fig = go.Figure(data=[go.Pie(labels=labels,
                                values=values,
                                marker_colors=colors,
                                hole=.3, # Optionnel: pour un style "donut"
                                pull=[0, 0.1] # Optionnel: détacher légèrement la part du surplus
                                )])

    fig.update_traces(textinfo='percent+label+value', textfont_size=12,
                    hovertemplate="<b>%{label}</b><br>Quantité: %{value:,.0f} kWh<br>Pourcentage: %{percent}<extra></extra>")

    fig.update_layout(
        title_text="Répartition de l'Énergie Produite: Autoconsommation vs Surplus",
        legend_title_text="Catégories",
        # Optionnel: Cacher la légende si les labels sur le camembert suffisent
        # showlegend=False
    )

    return fig