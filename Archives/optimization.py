import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random

class OptimizationModule:
    def __init__(self):
        # Initialiser les structures de données si elles n'existent pas
        if 'optimization_results' not in st.session_state:
            st.session_state.optimization_results = {}
        
        if 'monte_carlo_results' not in st.session_state:
            st.session_state.monte_carlo_results = {}
    
    def optimize_selling_price(self, scenario_name, economic_analysis_module):
        """
        Optimise le prix de revente pour un scénario donné
        
        Args:
            scenario_name: Nom du scénario à optimiser
            economic_analysis_module: Instance du module d'analyse économique
            
        Returns:
            dict: Dictionnaire contenant les résultats de l'optimisation
        """
        # Récupérer les paramètres de configuration
        config = st.session_state.config
        
        # Paramètres d'optimisation
        prix_min = config['prix_min_revente']
        prix_max = config['prix_max_revente']
        pas = config['pas_optimisation']
        
        # Créer un tableau de prix à tester
        prix_a_tester = np.arange(prix_min, prix_max + pas, pas)
        
        # Initialiser les résultats
        resultats = {}
        
        # Tester chaque prix
        for prix in prix_a_tester:
            st.write(f"Test du prix : {prix:.4f}...") # Affiche dans l'UI Streamlit
            print(f"Test du prix : {prix:.4f}...")   # Affiche dans la console CMD
            
            # Calculer les indicateurs financiers pour ce prix
            resultats[prix] = economic_analysis_module.calculate_financial_indicators(scenario_name, prix_revente=prix)
        
        # Initialiser les variables pour l'optimisation
        prix_optimal = None
        indicateurs_optimaux = None
        score_max = -float('inf')
        
        # Critères de rentabilité
        roi_min = 0.05  # 5%
        irr_min = 0.04  # 4%
        payback_max = 15  # 15 ans
        dscr_min = config['target_dscr']
        tarif_edf = config['tarif_edf_reference']
        
        # Fonctions d'évaluation des indicateurs (normalisées entre 0 et 1)
        def eval_roi(roi):
            if roi <= 0:
                return 0
            elif roi >= 0.15:  # ROI max pris en compte (15%)
                return 1
            else:
                return roi / 0.15
        
        def eval_irr(irr):
            if irr is None or irr <= 0:
                return 0
            elif irr >= 0.12:  # TRI max pris en compte (12%)
                return 1
            else:
                return irr / 0.12
        
        def eval_payback(payback):
            if payback == float('inf') or payback >= 25:
                return 0
            elif payback <= 5:  # Payback idéal (5 ans)
                return 1
            else:
                return 1 - (payback - 5) / 20
        
        def eval_dscr(dscr):
            if dscr < dscr_min:
                return 0
            elif dscr >= 2:  # DSCR max pris en compte (2)
                return 1
            else:
                return (dscr - dscr_min) / (2 - dscr_min)
        
        def eval_competitive(prix):
            if prix >= tarif_edf:
                return 0
            else:
                return 1 - prix / tarif_edf
        
        # Pour chaque prix, évaluer les indicateurs et calculer un score global
        for prix, res in resultats.items():
            # Vérifier que les résultats sont valides
            if res is None:
                continue
            
            # Évaluer chaque indicateur
            score_roi = eval_roi(res['roi'])
            score_irr = eval_irr(res['irr'])
            score_payback = eval_payback(res['payback_period'])
            score_dscr = eval_dscr(res['avg_dscr'])
            score_competitive = eval_competitive(prix)
            
            # Calculer un score global pondéré
            # Pondérations (totale = 1)
            w_roi = 0.25
            w_irr = 0.2
            w_payback = 0.15
            w_dscr = 0.2
            w_competitive = 0.2
            
            score_global = (
                w_roi * score_roi +
                w_irr * score_irr +
                w_payback * score_payback +
                w_dscr * score_dscr +
                w_competitive * score_competitive
            )
            
            # Mettre à jour le prix optimal si le score est meilleur
            if score_global > score_max:
                score_max = score_global
                prix_optimal = prix
                indicateurs_optimaux = res.copy()
                indicateurs_optimaux['scores'] = {
                    'score_global': score_global,
                    'score_roi': score_roi,
                    'score_irr': score_irr,
                    'score_payback': score_payback,
                    'score_dscr': score_dscr,
                    'score_competitive': score_competitive
                }
        
        # Résultats de l'optimisation
        resultats_optimisation = {
            'scenario_name': scenario_name,
            'prix_optimal': prix_optimal,
            'indicateurs_optimaux': indicateurs_optimaux,
            'tous_resultats': resultats,
            'prix_testes': list(prix_a_tester)
        }
        
        return resultats_optimisation
    
    def run_monte_carlo_simulation(self, scenario_name, economic_analysis_module, prix_revente=None):
        """
        Exécute une simulation Monte Carlo pour évaluer la robustesse des résultats
        
        Args:
            scenario_name: Nom du scénario à utiliser
            economic_analysis_module: Instance du module d'analyse économique
            prix_revente: Prix de revente à utiliser (si None, utilise le prix optimal)
            
        Returns:
            dict: Dictionnaire contenant les résultats de la simulation Monte Carlo
        """
        # Récupérer les paramètres de configuration
        config = st.session_state.config
        
        # Nombre d'itérations
        n_iterations = config['nb_iterations_monte_carlo']
        
        # Écarts-types pour les variations
        ecart_type_production = config['ecart_type_production'] / 100  # Conversion en proportion
        ecart_type_consommation = config['ecart_type_consommation'] / 100  # Conversion en proportion
        
        # Si prix_revente est None, utiliser le prix optimal s'il existe
        if prix_revente is None:
            if scenario_name in st.session_state.optimization_results:
                prix_revente = st.session_state.optimization_results[scenario_name]['prix_optimal']
            else:
                prix_revente = config['prix_vente_initial']
        
        # Récupérer le scénario
        scenario = st.session_state.scenarios[scenario_name]
        
        # Initialiser les tableaux pour stocker les résultats
        roi_values = []
        irr_values = []
        npv_values = []
        payback_values = []
        dscr_values = []
        
        # Sauvegarder les données originales
        original_production_data = st.session_state.processed_data.copy()
        
        # Pour chaque itération
        for i in range(n_iterations):
            # Créer une copie des données
            simulated_data = original_production_data.copy()
            
            # Appliquer des variations aléatoires à la production et à la consommation
            # Variation suivant une loi normale avec l'écart-type défini
            prod_variation = np.random.normal(1, ecart_type_production)
            cons_variation = np.random.normal(1, ecart_type_consommation)
            
            # Appliquer les variations (avec un minimum de 0)
            simulated_data['production_kwh'] = (simulated_data['production_kwh'] * prod_variation).clip(lower=0)
            simulated_data['consumption_kwh'] = (simulated_data['consumption_kwh'] * cons_variation).clip(lower=0)
            
            # Recalculer l'autoconsommation
            simulated_data['autoconsumption_kwh'] = simulated_data.apply(
                lambda row: min(row['production_kwh'], row['consumption_kwh']), axis=1
            )
            
            # Recalculer le surplus
            simulated_data['surplus_kwh'] = simulated_data['production_kwh'] - simulated_data['autoconsumption_kwh']
            
            # Sauvegarder temporairement les données simulées
            temp_data = st.session_state.processed_data
            st.session_state.processed_data = simulated_data
            
            # Calculer les indicateurs financiers avec le prix de revente donné
            results = economic_analysis_module.simulate_selling_price(scenario_name, prix_revente)
            
            # Restaurer les données originales
            st.session_state.processed_data = temp_data
            
            # Stocker les résultats
            if results is not None:
                roi_values.append(results['roi'])
                irr_values.append(results['irr'] if results['irr'] is not None else 0)
                npv_values.append(results['npv'])
                payback_values.append(results['payback_period'] if results['payback_period'] != float('inf') else 30)
                dscr_values.append(results['avg_dscr'] if results['avg_dscr'] != float('inf') else 5)
        
        # Calculer les statistiques
        roi_mean = np.mean(roi_values)
        roi_std = np.std(roi_values)
        roi_percentiles = np.percentile(roi_values, [5, 25, 50, 75, 95])
        
        irr_mean = np.mean(irr_values)
        irr_std = np.std(irr_values)
        irr_percentiles = np.percentile(irr_values, [5, 25, 50, 75, 95])
        
        npv_mean = np.mean(npv_values)
        npv_std = np.std(npv_values)
        npv_percentiles = np.percentile(npv_values, [5, 25, 50, 75, 95])
        
        payback_mean = np.mean(payback_values)
        payback_std = np.std(payback_values)
        payback_percentiles = np.percentile(payback_values, [5, 25, 50, 75, 95])
        
        dscr_mean = np.mean(dscr_values)
        dscr_std = np.std(dscr_values)
        dscr_percentiles = np.percentile(dscr_values, [5, 25, 50, 75, 95])
        
        # Calculer les probabilités de succès
        roi_min = 0.05  # 5%
        irr_min = 0.04  # 4%
        payback_max = 15  # 15 ans
        dscr_min = config['target_dscr']
        
        prob_roi_success = np.mean(np.array(roi_values) >= roi_min)
        prob_irr_success = np.mean(np.array(irr_values) >= irr_min)
        prob_payback_success = np.mean(np.array(payback_values) <= payback_max)
        prob_dscr_success = np.mean(np.array(dscr_values) >= dscr_min)
        
        # Probabilité de succès global (tous les critères respectés)
        prob_global_success = np.mean(
            (np.array(roi_values) >= roi_min) &
            (np.array(irr_values) >= irr_min) &
            (np.array(payback_values) <= payback_max) &
            (np.array(dscr_values) >= dscr_min)
        )
        
        # Résultats de la simulation Monte Carlo
        monte_carlo_results = {
            'scenario_name': scenario_name,
            'prix_revente': prix_revente,
            'n_iterations': n_iterations,
            'ecart_type_production': ecart_type_production,
            'ecart_type_consommation': ecart_type_consommation,
            'roi_values': roi_values,
            'irr_values': irr_values,
            'npv_values': npv_values,
            'payback_values': payback_values,
            'dscr_values': dscr_values,
            'statistics': {
                'roi': {
                    'mean': roi_mean,
                    'std': roi_std,
                    'percentiles': roi_percentiles
                },
                'irr': {
                    'mean': irr_mean,
                    'std': irr_std,
                    'percentiles': irr_percentiles
                },
                'npv': {
                    'mean': npv_mean,
                    'std': npv_std,
                    'percentiles': npv_percentiles
                },
                'payback': {
                    'mean': payback_mean,
                    'std': payback_std,
                    'percentiles': payback_percentiles
                },
                'dscr': {
                    'mean': dscr_mean,
                    'std': dscr_std,
                    'percentiles': dscr_percentiles
                }
            },
            'probabilities': {
                'roi': prob_roi_success,
                'irr': prob_irr_success,
                'payback': prob_payback_success,
                'dscr': prob_dscr_success,
                'global': prob_global_success
            }
        }
        
        return monte_carlo_results
    
    def show_ui(self):
        """Affiche l'interface utilisateur du module d'optimisation"""
        st.markdown("<h1 class='main-header'>Optimisation du Prix de Revente</h1>", unsafe_allow_html=True)
        
        # Vérifier que les données nécessaires sont disponibles
        if not st.session_state.data_imported:
            st.warning("Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'onglet 'Importation Données'.")
            return
        
        # Créer des onglets pour les différentes analyses
        tab1, tab2, tab3 = st.tabs(["Optimisation du Prix", "Simulation Monte Carlo", "Résultats Combinés"])
        
        with tab1:
            st.markdown("<h3 class='sub-header'>Optimisation du Prix de Revente</h3>", unsafe_allow_html=True)
            
            # Sélectionner le scénario à optimiser
            scenario = st.selectbox(
                "Sélectionnez un scénario",
                options=list(st.session_state.scenarios.keys()),
                index=0,
                key="optimization_scenario"
            )
            
            # Options d'optimisation
            with st.expander("Options d'optimisation avancées"):
                col1, col2 = st.columns(2)
                
                with col1:
                    prix_min = st.number_input(
                        "Prix minimum (€/kWh)",
                        min_value=0.05,
                        max_value=0.20,
                        value=st.session_state.config['prix_min_revente'],
                        step=0.01,
                        key="opt_prix_min"
                    )
                    
                    prix_max = st.number_input(
                        "Prix maximum (€/kWh)",
                        min_value=prix_min,
                        max_value=0.30,
                        value=st.session_state.config['prix_max_revente'],
                        step=0.01,
                        key="opt_prix_max"
                    )
                
                with col2:
                    pas = st.number_input(
                        "Pas d'optimisation (€/kWh)",
                        min_value=0.001,
                        max_value=0.01,
                        value=st.session_state.config['pas_optimisation'],
                        step=0.001,
                        key="opt_pas"
                    )
                
                # Mettre à jour la configuration
                st.session_state.config['prix_min_revente'] = prix_min
                st.session_state.config['prix_max_revente'] = prix_max
                st.session_state.config['pas_optimisation'] = pas
            
            # Bouton pour lancer l'optimisation
            if st.button("Lancer l'optimisation du prix de revente", key="run_optimization"):
                with st.spinner("Optimisation en cours..."):
                    # Importer le module d'analyse économique
                    from modules.economic_analysis import EconomicAnalysisModule
                    economic_module = EconomicAnalysisModule()
                    
                    # Lancer l'optimisation
                    results = self.optimize_selling_price(scenario, economic_module)
                    
                    if results:
                        # Stocker les résultats dans la session
                        st.session_state.optimization_results[scenario] = results
                        st.session_state.optimization_completed = True
            
            # Si des résultats existent déjà pour ce scénario, les afficher
            if scenario in st.session_state.optimization_results:
                self.display_optimization_results(st.session_state.optimization_results[scenario])
        
        with tab2:
            st.markdown("<h3 class='sub-header'>Simulation Monte Carlo</h3>", unsafe_allow_html=True)
            
            # Sélectionner le scénario pour la simulation
            scenario = st.selectbox(
                "Sélectionnez un scénario",
                options=list(st.session_state.scenarios.keys()),
                index=0,
                key="monte_carlo_scenario"
            )
            
            # Options de la simulation
            with st.expander("Options de la simulation Monte Carlo"):
                col1, col2 = st.columns(2)
                
                with col1:
                    n_iterations = st.number_input(
                        "Nombre d'itérations",
                        min_value=100,
                        max_value=10000,
                        value=st.session_state.config['nb_iterations_monte_carlo'],
                        step=100,
                        key="mc_iterations"
                    )
                    
                    # Mode de sélection du prix de revente
                    prix_source = st.radio(
                        "Source du prix de revente",
                        options=["Prix optimal", "Prix personnalisé"],
                        index=0,
                        key="mc_prix_source"
                    )
                
                with col2:
                    ecart_type_production = st.slider(
                        "Écart-type Production (%)",
                        min_value=1.0,
                        max_value=30.0,
                        value=st.session_state.config['ecart_type_production'],
                        step=1.0,
                        key="mc_ecart_type_prod"
                    )
                    
                    ecart_type_consommation = st.slider(
                        "Écart-type Consommation (%)",
                        min_value=1.0,
                        max_value=30.0,
                        value=st.session_state.config['ecart_type_consommation'],
                        step=1.0,
                        key="mc_ecart_type_cons"
                    )
                
                # Si prix personnalisé, demander la valeur
                prix_revente = None
                if prix_source == "Prix personnalisé":
                    prix_revente = st.number_input(
                        "Prix de revente personnalisé (€/kWh)",
                        min_value=0.05,
                        max_value=0.30,
                        value=st.session_state.config['prix_vente_initial'],
                        step=0.01,
                        key="mc_prix_perso"
                    )
                
                # Mettre à jour la configuration
                st.session_state.config['nb_iterations_monte_carlo'] = n_iterations
                st.session_state.config['ecart_type_production'] = ecart_type_production
                st.session_state.config['ecart_type_consommation'] = ecart_type_consommation
            
            # Bouton pour lancer la simulation
            if st.button("Lancer la simulation Monte Carlo", key="run_monte_carlo"):
                with st.spinner("Simulation en cours..."):
                    # Vérifier que le scénario a été optimisé si on veut utiliser le prix optimal
                    if prix_source == "Prix optimal" and scenario not in st.session_state.optimization_results:
                        st.error("Veuillez d'abord optimiser ce scénario dans l'onglet 'Optimisation du Prix'.")
                    else:
                        # Importer le module d'analyse économique
                        from modules.economic_analysis import EconomicAnalysisModule
                        economic_module = EconomicAnalysisModule()
                        
                        # Afficher une barre de progression
                        progress_bar = st.progress(0)
                        
                        # Simuler une barre de progression (car la simulation réelle est difficile à suivre)
                        for i in range(10):
                            # Actualiser la barre de progression
                            progress_bar.progress((i + 1) / 10)
                            time.sleep(0.2)
                        
                        # Lancer la simulation
                        results = self.run_monte_carlo_simulation(scenario, economic_module, prix_revente)
                        
                        # Terminer la barre de progression
                        progress_bar.progress(1.0)
                        
                        if results:
                            # Stocker les résultats dans la session
                            st.session_state.monte_carlo_results[scenario] = results
                            
                            # Afficher les résultats
                            self.display_monte_carlo_results(results)
            
            # Si des résultats existent déjà pour ce scénario, les afficher
            if scenario in st.session_state.monte_carlo_results:
                self.display_monte_carlo_results(st.session_state.monte_carlo_results[scenario])
        
        with tab3:
            st.markdown("<h3 class='sub-header'>Résultats Combinés</h3>", unsafe_allow_html=True)
            
            # Vérifier que des résultats existent
            if not st.session_state.optimization_results:
                st.info("Aucun résultat d'optimisation disponible. Veuillez d'abord optimiser un scénario dans l'onglet 'Optimisation du Prix'.")
                return
            
            # Sélectionner les scénarios à comparer
            scenarios_with_results = [s for s in st.session_state.scenarios.keys() if s in st.session_state.optimization_results]
            
            if not scenarios_with_results:
                st.info("Aucun scénario n'a encore été optimisé.")
                return
            
            scenarios_to_compare = st.multiselect(
                "Sélectionnez les scénarios à comparer",
                options=scenarios_with_results,
                default=scenarios_with_results[:min(3, len(scenarios_with_results))],
                key="combined_scenarios"
            )
            
            if scenarios_to_compare:
                # Afficher les résultats combinés
                self.display_combined_results(scenarios_to_compare)
    
    def display_optimization_results(self, results):
        """
        Affiche les résultats de l'optimisation
        
        Args:
            results: Dictionnaire contenant les résultats de l'optimisation
        """
        st.markdown("### Résultats de l'Optimisation du Prix de Revente")
        
        # Extraire les données
        scenario_name = results['scenario_name']
        prix_optimal = results['prix_optimal']
        indicateurs = results['indicateurs_optimaux']
        
        # Afficher le prix optimal
        st.markdown(f"<div class='success-box'>Le prix de revente optimal pour le scénario <b>{scenario_name}</b> est de <b>{prix_optimal:.4f} €/kWh</b></div>", unsafe_allow_html=True)
        
        # Afficher les indicateurs financiers clés
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("ROI", f"{indicateurs['roi']*100:.2f}%")
            st.markdown(f"Score: {indicateurs['scores']['score_roi']:.2f}")
        
        with col2:
            st.metric("TRI (IRR)", f"{indicateurs['irr']*100:.2f}%" if indicateurs['irr'] is not None else "Non calculable")
            st.markdown(f"Score: {indicateurs['scores']['score_irr']:.2f}")
        
        with col3:
            st.metric("Période de Récupération", f"{indicateurs['payback_period']:.2f} ans" if indicateurs['payback_period'] != float('inf') else "Jamais")
            st.markdown(f"Score: {indicateurs['scores']['score_payback']:.2f}")
        
        with col4:
            st.metric("DSCR moyen", f"{indicateurs['avg_dscr']:.2f}")
            st.markdown(f"Score: {indicateurs['scores']['score_dscr']:.2f}")
        
        # Afficher le score global
        st.markdown(f"<div class='info-box'>Score global d'optimisation: <b>{indicateurs['scores']['score_global']:.4f}</b></div>", unsafe_allow_html=True)
        
        # Afficher un graphique des résultats en fonction du prix
        st.markdown("### Indicateurs Financiers en Fonction du Prix de Revente")
        
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
        
        # Graphique ROI et TRI en fonction du prix
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["ROI (%)"],
            name='ROI (%)',
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig1.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["TRI (%)"],
            name='TRI (%)',
            mode='lines+markers',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))
        
        # Ajouter une ligne verticale pour le prix optimal
        fig1.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results[["ROI (%)", "TRI (%)"]].max().max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        # Ajouter une annotation pour le prix optimal
        fig1.add_annotation(
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
            align="center"
        )
        
        fig1.update_layout(
            title="ROI et TRI en fonction du Prix de Revente",
            xaxis_title="Prix de Revente (€/kWh)",
            yaxis_title="Pourcentage (%)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig1, use_container_width=True, key=f"optim_roi_tri_{scenario_name}")
        
        # Graphique VAN et Période de Récupération en fonction du prix
        fig2 = go.Figure()
        
        # Première courbe: VAN
        fig2.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["VAN (€)"],
            name='VAN (€)',
            mode='lines+markers',
            line=dict(color='purple', width=2),
            marker=dict(size=6),
            yaxis="y"
        ))
        
        # Seconde courbe: Période de Récupération
        fig2.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["Période de Récupération (ans)"],
            name='Période de Récupération (ans)',
            mode='lines+markers',
            line=dict(color='orange', width=2),
            marker=dict(size=6),
            yaxis="y2"
        ))
        
        # Ajouter une ligne verticale pour le prix optimal
        fig2.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results["VAN (€)"].max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        fig2.update_layout(
            title="VAN et Période de Récupération en fonction du Prix de Revente",
            xaxis_title="Prix de Revente (€/kWh)",
            yaxis=dict(
                title="VAN (€)",
                side="left"
            ),
            yaxis2=dict(
                title="Période de Récupération (ans)",
                side="right",
                overlaying="y"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig2, use_container_width=True, key=f"optim_van_payback_{scenario_name}")
        
        # Graphique DSCR en fonction du prix
        fig3 = go.Figure()
        
        fig3.add_trace(go.Scatter(
            x=df_results["Prix (€/kWh)"],
            y=df_results["DSCR moyen"],
            name='DSCR moyen',
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(size=6)
        ))
        
        # Ajouter une ligne horizontale pour le DSCR cible
        target_dscr = st.session_state.config['target_dscr']
        fig3.add_shape(
            type="line",
            x0=df_results["Prix (€/kWh)"].min(),
            y0=target_dscr,
            x1=df_results["Prix (€/kWh)"].max(),
            y1=target_dscr,
            line=dict(
                color="green",
                width=2,
                dash="dash",
            )
        )
        
        # Ajouter une ligne verticale pour le prix optimal
        fig3.add_shape(
            type="line",
            x0=prix_optimal,
            y0=0,
            x1=prix_optimal,
            y1=df_results["DSCR moyen"].max() * 1.1,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        fig3.update_layout(
            title="DSCR moyen en fonction du Prix de Revente",
            xaxis_title="Prix de Revente (€/kWh)",
            yaxis_title="DSCR moyen"
        )
        
        st.plotly_chart(fig3, use_container_width=True, key=f"optim_dscr_{scenario_name}")
        
        # Afficher le tableau des résultats
        with st.expander("Tableau détaillé des résultats"):
            st.dataframe(df_results.sort_values("Prix (€/kWh)"), use_container_width=True)
        
        # Afficher une analyse comparative avec le tarif EDF
        st.markdown("### Analyse Comparative avec le Tarif EDF")
        
        # Récupérer le tarif EDF
        tarif_edf = st.session_state.config['tarif_edf_reference']
        
        # Calculer l'écart avec le tarif EDF
        ecart_edf = tarif_edf - prix_optimal
        ecart_pct = (ecart_edf / tarif_edf) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Tarif EDF de référence", f"{tarif_edf:.4f} €/kWh")
            st.metric("Prix de revente optimal", f"{prix_optimal:.4f} €/kWh")
        
        with col2:
            st.metric("Écart absolu", f"{ecart_edf:.4f} €/kWh")
            st.metric("Écart relatif", f"{ecart_pct:.2f}%")
        
        if prix_optimal < tarif_edf:
            st.success(f"✅ Le prix de revente optimal ({prix_optimal:.4f} €/kWh) est compétitif par rapport au tarif EDF ({tarif_edf:.4f} €/kWh).")
            st.markdown(f"Avantage concurrentiel: **{ecart_pct:.2f}%** de moins que le tarif EDF.")
        else:
            st.error(f"❌ Le prix de revente optimal ({prix_optimal:.4f} €/kWh) n'est pas compétitif par rapport au tarif EDF ({tarif_edf:.4f} €/kWh).")
            st.markdown(f"Désavantage concurrentiel: **{-ecart_pct:.2f}%** de plus que le tarif EDF.")
    
    def display_monte_carlo_results(self, results):
        """
        Affiche les résultats de la simulation Monte Carlo
        
        Args:
            results: Dictionnaire contenant les résultats de la simulation
        """
        st.markdown("### Résultats de la Simulation Monte Carlo")
        
        # Extraire les données
        scenario_name = results['scenario_name']
        prix_revente = results['prix_revente']
        n_iterations = results['n_iterations']
        ecart_type_production = results['ecart_type_production']
        ecart_type_consommation = results['ecart_type_consommation']
        
        # Statistiques
        stats = results['statistics']
        probas = results['probabilities']
        
        # Afficher les paramètres de la simulation
        st.markdown(f"<div class='info-box'>Simulation pour le scénario <b>{scenario_name}</b> avec un prix de revente de <b>{prix_revente:.4f} €/kWh</b></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nombre d'itérations", f"{n_iterations}")
        
        with col2:
            st.metric("Écart-type Production", f"{ecart_type_production*100:.1f}%")
        
        with col3:
            st.metric("Écart-type Consommation", f"{ecart_type_consommation*100:.1f}%")
        
        # Afficher les probabilités de succès
        st.markdown("### Probabilités de Succès")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("ROI > 5%", f"{probas['roi']*100:.1f}%")
        
        with col2:
            st.metric("TRI > 4%", f"{probas['irr']*100:.1f}%")
        
        with col3:
            st.metric("Récupération < 15 ans", f"{probas['payback']*100:.1f}%")
        
        with col4:
            st.metric(f"DSCR > {st.session_state.config['target_dscr']}", f"{probas['dscr']*100:.1f}%")
        
        # Afficher la probabilité de succès global
        st.markdown(f"<div class='success-box'>Probabilité de succès global (tous critères respectés): <b>{probas['global']*100:.1f}%</b></div>", unsafe_allow_html=True)
        
        # Afficher les distributions des indicateurs
        st.markdown("### Distributions des Indicateurs Financiers")
        
        # Créer des onglets pour les différentes distributions
        tab1, tab2, tab3, tab4 = st.tabs(["ROI", "TRI", "VAN et Période de Récupération", "DSCR"])
        
        with tab1:
            # Distribution du ROI
            fig = go.Figure()
            
            # Histogramme
            fig.add_trace(go.Histogram(
                x=results['roi_values'],
                name='Distribution',
                opacity=0.7,
                marker_color='blue',
                nbinsx=30
            ))
            
            # Ligne verticale pour la moyenne
            fig.add_shape(
                type="line",
                x0=stats['roi']['mean'],
                y0=0,
                x1=stats['roi']['mean'],
                y1=n_iterations / 10,  # Approximation de la hauteur
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                )
            )
            
            # Ligne verticale pour la valeur minimale acceptable
            fig.add_shape(
                type="line",
                x0=0.05,  # 5%
                y0=0,
                x1=0.05,
                y1=n_iterations / 10,
                line=dict(
                    color="green",
                    width=2,
                    dash="dash",
                )
            )
            
            # Annotations
            fig.add_annotation(
                x=stats['roi']['mean'],
                y=n_iterations / 10,
                text=f"Moyenne: {stats['roi']['mean']*100:.2f}%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(color="red")
            )
            
            fig.add_annotation(
                x=0.05,
                y=n_iterations / 20,
                text="Minimum: 5%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                font=dict(color="green")
            )
            
            fig.update_layout(
                title="Distribution du ROI",
                xaxis_title="ROI",
                yaxis_title="Fréquence",
                bargap=0.05
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques du ROI
            st.markdown("#### Statistiques du ROI")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Moyenne", f"{stats['roi']['mean']*100:.2f}%")
                st.metric("Écart-type", f"{stats['roi']['std']*100:.2f}%")
            
            with col2:
                st.metric("Médiane (P50)", f"{stats['roi']['percentiles'][2]*100:.2f}%")
                st.metric("Probabilité ROI > 5%", f"{probas['roi']*100:.1f}%")
            
            with col3:
                st.metric("P05", f"{stats['roi']['percentiles'][0]*100:.2f}%")
                st.metric("P95", f"{stats['roi']['percentiles'][4]*100:.2f}%")
        
        with tab2:
            # Distribution du TRI
            fig = go.Figure()
            
            # Histogramme
            fig.add_trace(go.Histogram(
                x=results['irr_values'],
                name='Distribution',
                opacity=0.7,
                marker_color='green',
                nbinsx=30
            ))
            
            # Ligne verticale pour la moyenne
            fig.add_shape(
                type="line",
                x0=stats['irr']['mean'],
                y0=0,
                x1=stats['irr']['mean'],
                y1=n_iterations / 10,
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                )
            )
            
            # Ligne verticale pour la valeur minimale acceptable
            fig.add_shape(
                type="line",
                x0=0.04,  # 4%
                y0=0,
                x1=0.04,
                y1=n_iterations / 10,
                line=dict(
                    color="green",
                    width=2,
                    dash="dash",
                )
            )
            
            # Annotations
            fig.add_annotation(
                x=stats['irr']['mean'],
                y=n_iterations / 10,
                text=f"Moyenne: {stats['irr']['mean']*100:.2f}%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(color="red")
            )
            
            fig.add_annotation(
                x=0.04,
                y=n_iterations / 20,
                text="Minimum: 4%",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                font=dict(color="green")
            )
            
            fig.update_layout(
                title="Distribution du TRI (IRR)",
                xaxis_title="TRI",
                yaxis_title="Fréquence",
                bargap=0.05
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques du TRI
            st.markdown("#### Statistiques du TRI")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Moyenne", f"{stats['irr']['mean']*100:.2f}%")
                st.metric("Écart-type", f"{stats['irr']['std']*100:.2f}%")
            
            with col2:
                st.metric("Médiane (P50)", f"{stats['irr']['percentiles'][2]*100:.2f}%")
                st.metric("Probabilité TRI > 4%", f"{probas['irr']*100:.1f}%")
            
            with col3:
                st.metric("P05", f"{stats['irr']['percentiles'][0]*100:.2f}%")
                st.metric("P95", f"{stats['irr']['percentiles'][4]*100:.2f}%")
        
        with tab3:
            # Onglet VAN et Période de Récupération
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution de la VAN
                fig = go.Figure()
                
                # Histogramme
                fig.add_trace(go.Histogram(
                    x=results['npv_values'],
                    name='Distribution',
                    opacity=0.7,
                    marker_color='purple',
                    nbinsx=30
                ))
                
                # Ligne verticale pour la moyenne
                fig.add_shape(
                    type="line",
                    x0=stats['npv']['mean'],
                    y0=0,
                    x1=stats['npv']['mean'],
                    y1=n_iterations / 10,
                    line=dict(
                        color="red",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Ligne verticale pour la valeur minimale acceptable (VAN > 0)
                fig.add_shape(
                    type="line",
                    x0=0,
                    y0=0,
                    x1=0,
                    y1=n_iterations / 10,
                    line=dict(
                        color="green",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Annotations
                fig.add_annotation(
                    x=stats['npv']['mean'],
                    y=n_iterations / 10,
                    text=f"Moyenne: {stats['npv']['mean']:,.2f} €",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    font=dict(color="red")
                )
                
                fig.update_layout(
                    title="Distribution de la VAN",
                    xaxis_title="VAN (€)",
                    yaxis_title="Fréquence",
                    bargap=0.05
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques de la VAN
                st.markdown("#### Statistiques de la VAN")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric("Moyenne", f"{stats['npv']['mean']:,.2f} €")
                    st.metric("Médiane (P50)", f"{stats['npv']['percentiles'][2]:,.2f} €")
                
                with col_b:
                    st.metric("Écart-type", f"{stats['npv']['std']:,.2f} €")
                    st.metric("Probabilité VAN > 0", f"{np.mean(np.array(results['npv_values']) > 0)*100:.1f}%")
            
            with col2:
                # Distribution de la Période de Récupération
                fig = go.Figure()
                
                # Histogramme
                fig.add_trace(go.Histogram(
                    x=results['payback_values'],
                    name='Distribution',
                    opacity=0.7,
                    marker_color='orange',
                    nbinsx=30
                ))
                
                # Ligne verticale pour la moyenne
                fig.add_shape(
                    type="line",
                    x0=stats['payback']['mean'],
                    y0=0,
                    x1=stats['payback']['mean'],
                    y1=n_iterations / 10,
                    line=dict(
                        color="red",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Ligne verticale pour la valeur maximale acceptable
                fig.add_shape(
                    type="line",
                    x0=15,  # 15 ans
                    y0=0,
                    x1=15,
                    y1=n_iterations / 10,
                    line=dict(
                        color="green",
                        width=2,
                        dash="dash",
                    )
                )
                
                # Annotations
                fig.add_annotation(
                    x=stats['payback']['mean'],
                    y=n_iterations / 10,
                    text=f"Moyenne: {stats['payback']['mean']:.2f} ans",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    font=dict(color="red")
                )
                
                fig.add_annotation(
                    x=15,
                    y=n_iterations / 20,
                    text="Maximum: 15 ans",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="green",
                    font=dict(color="green")
                )
                
                fig.update_layout(
                    title="Distribution de la Période de Récupération",
                    xaxis_title="Période de Récupération (ans)",
                    yaxis_title="Fréquence",
                    bargap=0.05
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistiques de la Période de Récupération
                st.markdown("#### Statistiques de la Période de Récupération")
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric("Moyenne", f"{stats['payback']['mean']:.2f} ans")
                    st.metric("Médiane (P50)", f"{stats['payback']['percentiles'][2]:.2f} ans")
                
                with col_b:
                    st.metric("Écart-type", f"{stats['payback']['std']:.2f} ans")
                    st.metric("Probabilité < 15 ans", f"{probas['payback']*100:.1f}%")
        
        with tab4:
            # Distribution du DSCR
            fig = go.Figure()
            
            # Histogramme
            fig.add_trace(go.Histogram(
                x=results['dscr_values'],
                name='Distribution',
                opacity=0.7,
                marker_color='red',
                nbinsx=30
            ))
            
            # Ligne verticale pour la moyenne
            fig.add_shape(
                type="line",
                x0=stats['dscr']['mean'],
                y0=0,
                x1=stats['dscr']['mean'],
                y1=n_iterations / 10,
                line=dict(
                    color="red",
                    width=2,
                    dash="dash",
                )
            )
            
            # Ligne verticale pour la valeur minimale acceptable
            target_dscr = st.session_state.config['target_dscr']
            fig.add_shape(
                type="line",
                x0=target_dscr,
                y0=0,
                x1=target_dscr,
                y1=n_iterations / 10,
                line=dict(
                    color="green",
                    width=2,
                    dash="dash",
                )
            )
            
            # Annotations
            fig.add_annotation(
                x=stats['dscr']['mean'],
                y=n_iterations / 10,
                text=f"Moyenne: {stats['dscr']['mean']:.2f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                font=dict(color="red")
            )
            
            fig.add_annotation(
                x=target_dscr,
                y=n_iterations / 20,
                text=f"Minimum: {target_dscr}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                font=dict(color="green")
            )
            
            fig.update_layout(
                title="Distribution du DSCR moyen",
                xaxis_title="DSCR moyen",
                yaxis_title="Fréquence",
                bargap=0.05
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistiques du DSCR
            st.markdown("#### Statistiques du DSCR")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Moyenne", f"{stats['dscr']['mean']:.2f}")
                st.metric("Écart-type", f"{stats['dscr']['std']:.2f}")
            
            with col2:
                st.metric("Médiane (P50)", f"{stats['dscr']['percentiles'][2]:.2f}")
                st.metric(f"Probabilité DSCR > {target_dscr}", f"{probas['dscr']*100:.1f}%")
            
            with col3:
                st.metric("P05", f"{stats['dscr']['percentiles'][0]:.2f}")
                st.metric("P95", f"{stats['dscr']['percentiles'][4]:.2f}")
        
        # Interprétation des résultats
        st.markdown("### Interprétation des Résultats")
        
        if probas['global'] >= 0.9:
            st.success(f"✅ Le projet est très robuste avec une probabilité de succès global de {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est recommandé.")
        elif probas['global'] >= 0.75:
            st.info(f"ℹ️ Le projet est robuste avec une probabilité de succès global de {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est acceptable.")
        elif probas['global'] >= 0.5:
            st.warning(f"⚠️ Le projet présente une robustesse modérée avec une probabilité de succès global de {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est risqué.")
        else:
            st.error(f"❌ Le projet n'est pas robuste avec une probabilité de succès global de seulement {probas['global']*100:.1f}%. Le prix de revente de {prix_revente:.4f} €/kWh est insuffisant.")
        
        # Recommandations
        st.markdown("#### Recommandations")
        
        if probas['roi'] < 0.8:
            st.markdown("- ⚠️ Le ROI présente un risque significatif. Envisagez d'augmenter le prix de revente ou de réduire les coûts.")
        
        if probas['irr'] < 0.8:
            st.markdown("- ⚠️ Le TRI présente un risque significatif. Envisagez d'améliorer la structure de financement.")
        
        if probas['payback'] < 0.8:
            st.markdown("- ⚠️ La période de récupération présente un risque significatif. Le retour sur investissement pourrait prendre plus de temps que prévu.")
        
        if probas['dscr'] < 0.8:
            st.markdown("- ⚠️ Le DSCR présente un risque significatif. Le service de la dette pourrait être compromis en cas de performance inférieure aux attentes.")
        
        if all(p >= 0.8 for p in [probas['roi'], probas['irr'], probas['payback'], probas['dscr']]):
            st.markdown("- ✅ Tous les indicateurs présentent une bonne robustesse. Le projet semble viable avec le prix de revente actuel.")
    
    def display_combined_results(self, scenarios):
        """
        Affiche les résultats combinés de plusieurs scénarios
        
        Args:
            scenarios: Liste des noms de scénarios à comparer
        """
        st.markdown("### Comparaison des Prix Optimaux par Scénario")
        
        # Créer un tableau pour comparer les prix optimaux
        data = []
        
        for scenario in scenarios:
            if scenario in st.session_state.optimization_results:
                results = st.session_state.optimization_results[scenario]
                
                # Extraire les données
                prix_optimal = results['prix_optimal']
                indicateurs = results['indicateurs_optimaux']
                
                # Ajouter les données au tableau
                data.append({
                    "Scénario": scenario,
                    "Prix Optimal (€/kWh)": prix_optimal,
                    "ROI (%)": indicateurs['roi'] * 100,
                    "TRI (%)": indicateurs['irr'] * 100 if indicateurs['irr'] is not None else None,
                    "Période de Récupération (ans)": indicateurs['payback_period'],
                    "DSCR moyen": indicateurs['avg_dscr'],
                    "Score Global": indicateurs['scores']['score_global']
                })
        
        df_comparison = pd.DataFrame(data)
        
        # Afficher le tableau
        st.dataframe(df_comparison.style.highlight_max(subset=['ROI (%)', 'TRI (%)', 'DSCR moyen', 'Score Global']).highlight_min(subset=['Prix Optimal (€/kWh)', 'Période de Récupération (ans)']), use_container_width=True)
        
        # Créer un graphique de comparaison des prix optimaux
        fig = go.Figure()
        
        # Barres pour les prix optimaux
        fig.add_trace(go.Bar(
            x=[d["Scénario"] for d in data],
            y=[d["Prix Optimal (€/kWh)"] for d in data],
            name='Prix Optimal (€/kWh)',
            marker_color='blue'
        ))
        
        # Ligne pour le tarif EDF
        tarif_edf = st.session_state.config['tarif_edf_reference']
        fig.add_trace(go.Scatter(
            x=[d["Scénario"] for d in data],
            y=[tarif_edf] * len(data),
            name=f'Tarif EDF ({tarif_edf} €/kWh)',
            mode='lines',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title="Prix de Revente Optimaux par Scénario",
            xaxis_title="Scénario",
            yaxis_title="Prix (€/kWh)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Afficher les résultats Monte Carlo si disponibles
        monte_carlo_scenarios = [s for s in scenarios if s in st.session_state.monte_carlo_results]
        
        if monte_carlo_scenarios:
            st.markdown("### Comparaison des Probabilités de Succès par Scénario")
            
            # Créer un tableau pour comparer les probabilités
            mc_data = []
            
            for scenario in monte_carlo_scenarios:
                results = st.session_state.monte_carlo_results[scenario]
                
                # Extraire les données
                prix_revente = results['prix_revente']
                probas = results['probabilities']
                
                # Ajouter les données au tableau
                mc_data.append({
                    "Scénario": scenario,
                    "Prix de Revente (€/kWh)": prix_revente,
                    "Probabilité ROI (%)": probas['roi'] * 100,
                    "Probabilité TRI (%)": probas['irr'] * 100,
                    "Probabilité Récupération (%)": probas['payback'] * 100,
                    "Probabilité DSCR (%)": probas['dscr'] * 100,
                    "Probabilité Globale (%)": probas['global'] * 100
                })
            
            df_mc_comparison = pd.DataFrame(mc_data)
            
            # Afficher le tableau
            st.dataframe(df_mc_comparison.style.highlight_max(subset=['Probabilité ROI (%)', 'Probabilité TRI (%)', 'Probabilité Récupération (%)', 'Probabilité DSCR (%)', 'Probabilité Globale (%)']), use_container_width=True)
            
            # Créer un graphique de comparaison des probabilités
            fig = go.Figure()
            
            # Barres pour chaque type de probabilité
            fig.add_trace(go.Bar(
                x=[d["Scénario"] for d in mc_data],
                y=[d["Probabilité ROI (%)"] for d in mc_data],
                name='ROI > 5%',
                marker_color='blue'
            ))
            
            fig.add_trace(go.Bar(
                x=[d["Scénario"] for d in mc_data],
                y=[d["Probabilité TRI (%)"] for d in mc_data],
                name='TRI > 4%',
                marker_color='green'
            ))
            
            fig.add_trace(go.Bar(
                x=[d["Scénario"] for d in mc_data],
                y=[d["Probabilité Récupération (%)"] for d in mc_data],
                name='Récupération < 15 ans',
                marker_color='orange'
            ))
            
            fig.add_trace(go.Bar(
                x=[d["Scénario"] for d in mc_data],
                y=[d["Probabilité DSCR (%)"] for d in mc_data],
                name=f'DSCR > {st.session_state.config["target_dscr"]}',
                marker_color='red'
            ))
            
            fig.add_trace(go.Bar(
                x=[d["Scénario"] for d in mc_data],
                y=[d["Probabilité Globale (%)"] for d in mc_data],
                name='Succès Global',
                marker_color='purple'
            ))
            
            fig.update_layout(
                title="Probabilités de Succès par Scénario (Simulation Monte Carlo)",
                xaxis_title="Scénario",
                yaxis_title="Probabilité (%)",
                barmode='group',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Recommandation finale
        st.markdown("### Recommandation Finale")
        
        # Trouver le scénario avec le meilleur score global
        if data:
            best_scenario = max(data, key=lambda x: x["Score Global"])
            best_scenario_name = best_scenario["Scénario"]
            best_price = best_scenario["Prix Optimal (€/kWh)"]
            
            st.markdown(f"<div class='success-box'>", unsafe_allow_html=True)
            st.markdown(f"D'après l'analyse des différents scénarios, le scénario <b>{best_scenario_name}</b> présente le meilleur compromis avec un prix de revente optimal de <b>{best_price:.4f} €/kWh</b>.", unsafe_allow_html=True)
            
            # Si des résultats Monte Carlo sont disponibles pour ce scénario
            if best_scenario_name in st.session_state.monte_carlo_results:
                mc_results = st.session_state.monte_carlo_results[best_scenario_name]
                global_prob = mc_results['probabilities']['global'] * 100
                
                st.markdown(f"La simulation Monte Carlo indique une probabilité de succès global de <b>{global_prob:.1f}%</b> pour ce scénario.", unsafe_allow_html=True)
                
                if global_prob >= 90:
                    st.markdown(f"Le projet présente une <b>très forte robustesse</b> face aux variations de production et de consommation.", unsafe_allow_html=True)
                elif global_prob >= 75:
                    st.markdown(f"Le projet présente une <b>bonne robustesse</b> face aux variations de production et de consommation.", unsafe_allow_html=True)
                elif global_prob >= 50:
                    st.markdown(f"Le projet présente une <b>robustesse modérée</b> face aux variations de production et de consommation.", unsafe_allow_html=True)
                else:
                    st.markdown(f"Le projet présente une <b>faible robustesse</b> face aux variations de production et de consommation.", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Points de vigilance
            if best_price >= tarif_edf:
                st.warning(f"⚠️ Le prix optimal ({best_price:.4f} €/kWh) est supérieur ou égal au tarif EDF ({tarif_edf:.4f} €/kWh), ce qui pourrait compromettre la compétitivité du projet.")
            
            # Recommandations supplémentaires
            st.markdown("#### Points d'attention et recommandations")
            
            st.markdown("""
            - Vérifiez que les hypothèses du scénario recommandé sont réalistes et adaptées au contexte du projet.
            - Assurez-vous que le prix de revente est acceptable pour les acheteurs locaux potentiels.
            - Envisagez de négocier des conditions de financement plus avantageuses pour améliorer la rentabilité.
            - Surveillez l'évolution du tarif EDF qui sert de référence pour la compétitivité.
            - Réalisez une étude de marché approfondie pour confirmer la demande locale d'électricité.
            """)
        else:
            st.info("Aucun résultat d'optimisation n'est disponible pour les scénarios sélectionnés.")