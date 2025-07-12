# modules/optimisation_analyse/visualisation_prix.py

import plotly.graph_objects as go
import pandas as pd
import numpy as np

def create_price_benefit_figure(df_data: pd.DataFrame, 
                                cout_prod: float, 
                                prix_edf: float, 
                                selected_price: float | None = None, 
                                optimal_price: float | None = None) -> go.Figure :
    """
    Crée la figure Plotly interactive Prix Vente vs Bénéfice Client.
    Ne montre plus la marge producteur/brute dans le hover.

    Args:
        df_data: DataFrame contenant les colonnes 'PrixVente', 'BeneficeClient', 
                 'PctEconomie'. Doit être trié par PrixVente.
        cout_prod: Coût de production interne (LCOE) en €/kWh.
        prix_edf: Prix de référence EDF en €/kWh.
        selected_price: Prix actuellement sélectionné par le slider (optionnel).
        optimal_price: Prix optimal trouvé par l'optimiseur (optionnel).

    Returns:
        go.Figure: L'objet figure Plotly prêt à être affiché.
        Ou None si df_data est invalide.
    """
    # --- DEBUT MODIFICATION: Vérifier colonnes sans la Marge ---
    required_cols = ['PrixVente', 'BeneficeClient', 'PctEconomie']
    if not isinstance(df_data, pd.DataFrame) or df_data.empty or not all(c in df_data.columns for c in required_cols):
        missing = [c for c in required_cols if c not in df_data.columns] if isinstance(df_data, pd.DataFrame) else required_cols
        print(f"ERREUR VISU: df_data invalide ou colonnes manquantes: {missing}.")
        return go.Figure(layout=go.Layout(title="Données insuffisantes pour le graphique"))
    # --- FIN MODIFICATION ---

    fig = go.Figure()

    # Courbe principale
    fig.add_trace(go.Scatter(
        x=df_data['PrixVente'],
        y=df_data['BeneficeClient'],
        mode='lines',
        name='Bénéfice Client vs EDF',
        line=dict(color='#63C5DA', width=3), # Couleur Aqua
        customdata=df_data[['PctEconomie']],
        hovertemplate=(
            "<b>Prix Vente: %{x:.4f} €/kWh</b><br>" +
            "Bénéfice Client: %{y:,.0f} €/an<br>" +
            "Économie vs EDF: %{customdata[0]:.1f}%" +
            "<extra></extra>"
        )
    ))

    # Lignes de référence
    fig.add_vline(x=cout_prod, line_width=2, line_dash="dash", line_color="#FFA07A",
                  annotation_text="Coût Prod (LCOE)", annotation_position="top left", annotation_font_color="#FFA07A")
    fig.add_vline(x=prix_edf, line_width=2, line_dash="dash", line_color="#E9967A",
                  annotation_text="Prix EDF", annotation_position="top right", annotation_font_color="#E9967A")
    fig.add_hline(y=0, line_width=1, line_dash="dot", line_color="grey")

    # Marqueur pour le prix sélectionné par le slider (si fourni)
    if selected_price is not None:
        try:
            # Interpoler pour trouver le bénéfice exact au point du slider
            interpolated_benefit = np.interp(selected_price, df_data['PrixVente'], df_data['BeneficeClient'])
            fig.add_trace(go.Scatter(
                x=[selected_price],
                y=[interpolated_benefit],
                mode='markers',
                marker=dict(color='#FF6347', size=12, symbol='star'), # Couleur Tomate, étoile
                name='Prix Sélectionné'
            ))
        except Exception as e:
             print(f"AVERTISSEMENT VISU: Impossible d'interpoler/ajouter marqueur sélectionné: {e}")


    # Marqueur pour le prix optimal (si fourni et différent du sélectionné)
    if optimal_price is not None:
         # Vérifier si différent pour éviter superposition exacte
         is_different = True
         if selected_price is not None:
              is_different = abs(optimal_price - selected_price) > 1e-5 
              
         if is_different:
            try:
                optimal_benefit = np.interp(optimal_price, df_data['PrixVente'], df_data['BeneficeClient'])
                fig.add_trace(go.Scatter(
                    x=[optimal_price], y=[optimal_benefit], mode='markers',
                    marker=dict(color='#32CD32', size=10, symbol='diamond'), # Vert Lime, diamant
                    name='Prix Optimal (Score Max)'
                ))
                # Annotation pour le prix optimal
                fig.add_annotation(
                    x=optimal_price, y=optimal_benefit,
                    text=f"Optimal: {optimal_price:.4f}€", showarrow=True, arrowhead=1,
                    font=dict(color="#32CD32"), align="left", yshift=10
                )
            except Exception as e:
                print(f"AVERTISSEMENT VISU: Impossible d'interpoler/ajouter marqueur optimal: {e}")


    # Mise en page finale
    fig.update_layout(
        # title="Impact du Prix de Vente sur le Bénéfice Client Annuel", # Titre géré par l'UI
        xaxis_title="Prix de Vente Proposé (€/kWh)",
        yaxis_title="Bénéfice Client Annuel vs EDF (€)",
        template="plotly_white",
        hovermode="x unified",
        xaxis=dict(tickformat=".3f"), # 3 décimales pour le prix
        yaxis=dict(tickformat=",.0f"), # Séparateur milliers pour bénéfice
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), # Légende en haut
        annotations=[] # Supprimer l'ancienne annotation
    )

    return fig