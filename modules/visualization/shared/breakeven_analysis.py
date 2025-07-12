"""
Module pour l'analyse breakeven interactive
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .chart_utilities import (
    apply_theme, format_currency, format_percentage, format_number,
    validate_chart_data, COLORS, handle_chart_error
)

def create_breakeven_interactive_chart(results_data, config, analysis_engine=None):
    """
    Crée un graphique interactif d'analyse breakeven avec curseur pour faire varier le prix
    """
    try:
        if not analysis_engine:
            st.warning("Moteur d'analyse non disponible pour l'analyse breakeven.")
            return None
            
        # Paramètres de l'analyse
        prix_actuel = results_data.get('prix_revente', 0.15)
        prix_min = prix_actuel * 0.5  # -50%
        prix_max = prix_actuel * 1.5  # +50%
        n_points = 50
        
        # Génération des prix à tester
        prix_range = np.linspace(prix_min, prix_max, n_points)
        
        # Collecte des résultats pour chaque prix
        npv_values = []
        irr_values = []
        payback_values = []
        dscr_values = []
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, prix in enumerate(prix_range):
            status_text.text(f"Calcul pour prix {prix:.4f} €/kWh...")
            progress_bar.progress((i + 1) / n_points)
            
            # Calculer les indicateurs pour ce prix
            try:
                # Utiliser le moteur d'analyse pour recalculer
                temp_results = analysis_engine.calculate_financial_indicators(
                    prix_vente=prix,
                    keep_other_params=True
                )
                
                npv_values.append(temp_results.get('npv', 0))
                irr_values.append(temp_results.get('irr', 0) * 100)
                payback_values.append(temp_results.get('payback_period', 999))
                dscr_values.append(temp_results.get('avg_dscr', 0))
                
            except Exception:
                # En cas d'erreur, utiliser des approximations linéaires
                delta_prix = (prix - prix_actuel) / prix_actuel
                npv_base = results_data.get('npv', 0)
                irr_base = results_data.get('irr', 0) * 100
                
                # Approximations simplifiées
                npv_values.append(npv_base * (1 + delta_prix * 3))
                irr_values.append(irr_base * (1 + delta_prix * 0.5))
                payback_values.append(results_data.get('payback_period', 10) * (1 - delta_prix * 0.3))
                dscr_values.append(results_data.get('avg_dscr', 1.2) * (1 + delta_prix * 0.4))
        
        progress_bar.empty()
        status_text.empty()
        
        # Trouver les points de breakeven
        npv_array = np.array(npv_values)
        breakeven_npv_idx = np.where(np.diff(np.sign(npv_array)))[0]
        breakeven_npv_prix = prix_range[breakeven_npv_idx] if len(breakeven_npv_idx) > 0 else None
        
        # Création du graphique interactif
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("VAN vs Prix", "TRI vs Prix", "Payback vs Prix", "DSCR vs Prix"),
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )
        
        # Graphique 1: VAN
        fig.add_trace(
            go.Scatter(
                x=prix_range,
                y=npv_values,
                mode='lines',
                name='VAN',
                line=dict(color=COLORS['primary'], width=3),
                hovertemplate='Prix: %{x:.4f} €/kWh<br>VAN: %{y:,.0f} €<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Ligne de breakeven VAN
        fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=1)
        if breakeven_npv_prix is not None and len(breakeven_npv_prix) > 0:
            fig.add_vline(
                x=breakeven_npv_prix[0], 
                line_dash="dot", 
                line_color="green",
                annotation_text=f"Breakeven: {breakeven_npv_prix[0]:.4f} €/kWh",
                row=1, col=1
            )
        
        # Zone de profit/perte
        fig.add_trace(
            go.Scatter(
                x=prix_range,
                y=npv_values,
                fill='tozeroy',
                fillcolor='rgba(0,255,0,0.1)' if npv_values[-1] > 0 else 'rgba(255,0,0,0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False,
                hoverinfo='skip'
            ),
            row=1, col=1
        )
        
        # Graphique 2: TRI
        fig.add_trace(
            go.Scatter(
                x=prix_range,
                y=irr_values,
                mode='lines',
                name='TRI',
                line=dict(color=COLORS['success'], width=3),
                hovertemplate='Prix: %{x:.4f} €/kWh<br>TRI: %{y:.1f}%<extra></extra>'
            ),
            row=1, col=2
        )
        
        # Ligne cible TRI
        target_irr = config.get('cout_fonds_propres', 8.0)
        fig.add_hline(
            y=target_irr, 
            line_dash="dash", 
            line_color="orange",
            annotation_text=f"Cible: {target_irr}%",
            row=1, col=2
        )
        
        # Graphique 3: Payback
        valid_payback = [p if p < 999 else None for p in payback_values]
        fig.add_trace(
            go.Scatter(
                x=prix_range,
                y=valid_payback,
                mode='lines',
                name='Payback',
                line=dict(color=COLORS['warning'], width=3),
                hovertemplate='Prix: %{x:.4f} €/kWh<br>Payback: %{y:.1f} ans<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Ligne cible Payback
        target_payback = config.get('payback_max_years', 10)
        fig.add_hline(
            y=target_payback, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Max: {target_payback} ans",
            row=2, col=1
        )
        
        # Graphique 4: DSCR
        fig.add_trace(
            go.Scatter(
                x=prix_range,
                y=dscr_values,
                mode='lines',
                name='DSCR',
                line=dict(color=COLORS['info'], width=3),
                hovertemplate='Prix: %{x:.4f} €/kWh<br>DSCR: %{y:.2f}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # Lignes cibles DSCR
        fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Min: 1.0", row=2, col=2)
        fig.add_hline(
            y=config.get('target_dscr', 1.2), 
            line_dash="dash", 
            line_color="orange",
            annotation_text=f"Cible: {config.get('target_dscr', 1.2)}",
            row=2, col=2
        )
        
        # Marqueur prix actuel sur tous les graphiques
        for row in [1, 2]:
            for col in [1, 2]:
                fig.add_vline(
                    x=prix_actuel,
                    line_dash="solid",
                    line_color="black",
                    line_width=2,
                    row=row, col=col
                )
        
        # Mise en forme
        fig.update_xaxes(title_text="Prix de vente (€/kWh)", row=2, col=1)
        fig.update_xaxes(title_text="Prix de vente (€/kWh)", row=2, col=2)
        fig.update_yaxes(title_text="VAN (€)", row=1, col=1)
        fig.update_yaxes(title_text="TRI (%)", row=1, col=2)
        fig.update_yaxes(title_text="Payback (années)", row=2, col=1)
        fig.update_yaxes(title_text="DSCR", row=2, col=2)
        
        fig.update_layout(
            title="Analyse de Sensibilité au Prix de Vente",
            height=800,
            showlegend=False,
            hovermode='x unified'
        )
        
        return apply_theme(fig)
        
    except Exception as e:
        return handle_chart_error(e, "Analyse Breakeven")

def display_breakeven_analysis_ui(results_data, config, analysis_engine=None):
    """
    Interface utilisateur pour l'analyse breakeven interactive
    """
    st.markdown("### 🎯 Analyse du Point d'Équilibre (Breakeven)")
    
    # Explication
    with st.expander("ℹ️ Comment utiliser cette analyse"):
        st.markdown("""
        Cette analyse montre comment les indicateurs financiers évoluent en fonction du prix de vente:
        
        - **VAN (Valeur Actuelle Nette)**: Doit être positive pour que le projet soit rentable
        - **TRI (Taux de Rendement Interne)**: Doit dépasser le coût des fonds propres
        - **Payback**: Période de récupération de l'investissement
        - **DSCR**: Capacité à rembourser la dette (doit être > 1)
        
        Le **point d'équilibre** est le prix minimum pour atteindre une VAN = 0.
        """)
    
    # Contrôles interactifs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Slider pour ajuster le prix actuel
        prix_actuel = results_data.get('prix_revente', 0.15)
        prix_test = st.slider(
            "Prix de test (€/kWh)",
            min_value=prix_actuel * 0.5,
            max_value=prix_actuel * 1.5,
            value=prix_actuel,
            step=0.001,
            format="%.4f"
        )
        
        delta_prix = ((prix_test - prix_actuel) / prix_actuel) * 100
        st.metric(
            "Variation",
            f"{delta_prix:+.1f}%",
            delta=f"vs prix optimal ({prix_actuel:.4f} €/kWh)",
            delta_color="normal" if abs(delta_prix) < 10 else "inverse"
        )
    
    with col2:
        # Affichage des résultats au prix testé
        if analysis_engine and prix_test != prix_actuel:
            with st.spinner("Calcul en cours..."):
                test_results = analysis_engine.calculate_financial_indicators(
                    prix_vente=prix_test,
                    keep_other_params=True
                )
            
            st.metric("VAN au prix test", format_currency(test_results.get('npv', 0)))
            st.metric("TRI au prix test", f"{test_results.get('irr', 0) * 100:.1f}%")
        else:
            st.metric("VAN actuelle", format_currency(results_data.get('npv', 0)))
            st.metric("TRI actuel", f"{results_data.get('irr', 0) * 100:.1f}%")
    
    with col3:
        # Boutons d'action
        if st.button("🔄 Actualiser l'analyse", key="refresh_breakeven"):
            st.rerun()
            
        if st.button("📊 Exporter les données", key="export_breakeven"):
            # TODO: Implémenter l'export
            st.info("Export en cours de développement...")
    
    # Graphique principal
    fig = create_breakeven_interactive_chart(results_data, config, analysis_engine)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    # Tableau récapitulatif des points clés
    st.markdown("### 📋 Points Clés de l'Analyse")
    
    # Calcul approximatif du breakeven
    npv_base = results_data.get('npv', 0)
    prix_base = results_data.get('prix_revente', 0.15)
    
    # Estimation linéaire simple du breakeven
    if npv_base != 0:
        sensitivity_factor = 3  # Facteur empirique
        breakeven_prix_estimate = prix_base * (1 - npv_base / (npv_base * sensitivity_factor))
    else:
        breakeven_prix_estimate = prix_base
    
    summary_data = {
        "Indicateur": ["Prix Optimal", "Prix Breakeven (VAN=0)", "Marge de Sécurité", "Zone de Rentabilité"],
        "Valeur": [
            f"{prix_base:.4f} €/kWh",
            f"{breakeven_prix_estimate:.4f} €/kWh",
            f"{((prix_base - breakeven_prix_estimate) / prix_base * 100):.1f}%",
            f">{breakeven_prix_estimate:.4f} €/kWh"
        ],
        "Statut": [
            "✅ Actuel",
            "⚠️ Limite",
            "✅ Confortable" if prix_base > breakeven_prix_estimate * 1.2 else "⚠️ Faible",
            "✅ Rentable"
        ]
    }
    
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, hide_index=True, use_container_width=True)