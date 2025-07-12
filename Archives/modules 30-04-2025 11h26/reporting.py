import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import base64
from PIL import Image
import os
import pandas as pd
import numpy as np
import io
from datetime import datetime
import traceback

class ReportingModule:
    def __init__(self):
        # Initialiser les structures de données si elles n'existent pas
        if 'reports' not in st.session_state:
            st.session_state.reports = {}
    
    def create_summary_section(self):
        """
        Crée une section de résumé du projet
        
        Returns:
            str: HTML pour la section de résumé
        """
        if not st.session_state.data_imported:
            return "<p>Aucune donnée n'a été importée.</p>"
        
        # Obtenir les données clés
        config = st.session_state.config
        processed_data = st.session_state.processed_data
        
        # Calculer les statistiques clés
        total_production = processed_data['production_kwh'].sum() if processed_data is not None else 0
        total_consumption = processed_data['consumption_kwh'].sum() if processed_data is not None else 0
        total_autoconsumption = processed_data['autoconsumption_kwh'].sum() if processed_data is not None else 0
        total_surplus = processed_data['surplus_kwh'].sum() if processed_data is not None else 0
        
        autoconsumption_rate = (total_autoconsumption / total_production * 100) if total_production > 0 else 0
        autoproduction_rate = (total_autoconsumption / total_consumption * 100) if total_consumption > 0 else 0
        
        # Créer la section HTML
        html = """
        <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Résumé du Projet</h2>
            
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 300px; margin: 10px;">
                    <h3 style="color: #3498db;">Paramètres Économiques</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>CAPEX</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:,.2f} €</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>OPEX annuel</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:,.2f} €/an</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Durée PPA</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:.1f} ans</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Taux d'inflation</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:.2f}%</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Tarif EDF</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:.4f} €/kWh</td>
                        </tr>
                    </table>
                </div>
                
                <div style="flex: 1; min-width: 300px; margin: 10px;">
                    <h3 style="color: #e74c3c;">Statistiques Énergétiques</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Production Totale</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:,.2f} kWh</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Consommation Totale</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:,.2f} kWh</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Autoconsommation</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:,.2f} kWh</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Surplus</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:,.2f} kWh</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Taux d'autoconsommation</strong></td>
                            <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{:.2f}%</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
        """.format(
            config['capex'], 
            config['opex'], 
            config['duree_ppa'] / 12,
            config['taux_inflation'],
            config['tarif_edf_reference'],
            total_production,
            total_consumption,
            total_autoconsumption,
            total_surplus,
            autoconsumption_rate
        )
        
        return html
    
    def create_optimization_section(self):
        """
        Crée une section présentant les résultats d'optimisation
        
        Returns:
            str: HTML pour la section d'optimisation
        """
        if not hasattr(st.session_state, 'optimization_results') or not st.session_state.optimization_results:
            return "<p>Aucun résultat d'optimisation disponible.</p>"
        
        # Collecter les données
        optimization_data = []
        for scenario_name, scenario_results in st.session_state.optimization_results.items():
            # Récupérer les indicateurs optimaux
            indicateurs = scenario_results['indicateurs_optimaux']
            scenario_data = {
                'Scénario': scenario_name,
                'Prix Optimal (€/kWh)': scenario_results['prix_optimal'],
                'ROI (%)': indicateurs['roi'] * 100,
                'TRI (%)': indicateurs['irr'] * 100 if indicateurs['irr'] is not None else 0,
                'VAN (€)': indicateurs['npv'],
                'Période de Récupération (ans)': indicateurs['payback_period'] if indicateurs['payback_period'] != float('inf') else "N/A",
                'DSCR moyen': indicateurs['avg_dscr'],
                'Score Global': indicateurs['scores']['score_global']
            }
            optimization_data.append(scenario_data)
        
        # Trier par score global décroissant
        optimization_data.sort(key=lambda x: x['Score Global'], reverse=True)
        
        # Construire le tableau HTML
        table_rows = ""
        for data in optimization_data:
            table_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{data['Scénario']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['Prix Optimal (€/kWh)']:.4f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['ROI (%)']:.2f}%</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['TRI (%)']:.2f}%</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['VAN (€)']:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['Période de Récupération (ans)']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['DSCR moyen']:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['Score Global']:.4f}</td>
            </tr>
            """
        
        # Construire la section HTML
        html = f"""
        <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Résultats de l'Optimisation</h2>
            
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #3498db; color: white;">
                            <th style="padding: 12px; text-align: left;">Scénario</th>
                            <th style="padding: 12px; text-align: right;">Prix Optimal (€/kWh)</th>
                            <th style="padding: 12px; text-align: right;">ROI (%)</th>
                            <th style="padding: 12px; text-align: right;">TRI (%)</th>
                            <th style="padding: 12px; text-align: right;">VAN (€)</th>
                            <th style="padding: 12px; text-align: right;">Période de Récupération (ans)</th>
                            <th style="padding: 12px; text-align: right;">DSCR moyen</th>
                            <th style="padding: 12px; text-align: right;">Score Global</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #eaf2f8; border-radius: 5px;">
                <h3 style="color: #3498db;">Recommandation</h3>
                <p>Le scénario <strong>{optimization_data[0]['Scénario']}</strong> présente le meilleur score global ({optimization_data[0]['Score Global']:.4f}) avec un prix de revente optimal de <strong>{optimization_data[0]['Prix Optimal (€/kWh)']:.4f} €/kWh</strong>.</p>
                
                <p>Ce prix permet d'atteindre :</p>
                <ul>
                    <li>Un ROI de {optimization_data[0]['ROI (%)']:.2f}%</li>
                    <li>Un TRI de {optimization_data[0]['TRI (%)']:.2f}%</li>
                    <li>Une VAN de {optimization_data[0]['VAN (€)']:,.2f} €</li>
                    <li>Un DSCR moyen de {optimization_data[0]['DSCR moyen']:.2f}</li>
                </ul>
            </div>
        </div>
        """
        
        return html
    
    def create_monte_carlo_section(self):
        """
        Crée une section présentant les résultats des simulations Monte Carlo
        
        Returns:
            str: HTML pour la section Monte Carlo
        """
        if not hasattr(st.session_state, 'monte_carlo_results') or not st.session_state.monte_carlo_results:
            return "<p>Aucun résultat de simulation Monte Carlo disponible.</p>"
        
        # Collecter les données
        monte_carlo_data = []
        for scenario_name, scenario_results in st.session_state.monte_carlo_results.items():
            scenario_data = {
                'Scénario': scenario_name,
                'Prix de Revente (€/kWh)': scenario_results['prix_revente'],
                'ROI Moyen (%)': scenario_results['statistics']['roi']['mean'] * 100,
                'TRI Moyen (%)': scenario_results['statistics']['irr']['mean'] * 100,
                'VAN Moyenne (€)': scenario_results['statistics']['npv']['mean'],
                'Période de Récupération Moyenne (ans)': scenario_results['statistics']['payback']['mean'],
                'DSCR Moyen': scenario_results['statistics']['dscr']['mean'],
                'Probabilité ROI > 5% (%)': scenario_results['probabilities']['roi'] * 100,
                'Probabilité TRI > 4% (%)': scenario_results['probabilities']['irr'] * 100,
                'Probabilité DSCR > 1.15 (%)': scenario_results['probabilities']['dscr'] * 100,
                'Probabilité Succès Global (%)': scenario_results['probabilities']['global'] * 100
            }
            monte_carlo_data.append(scenario_data)
        
        # Trier par probabilité de succès global décroissante
        monte_carlo_data.sort(key=lambda x: x['Probabilité Succès Global (%)'], reverse=True)
        
        # Construire le tableau HTML
        table_rows = ""
        for data in monte_carlo_data:
            table_rows += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{data['Scénario']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['Prix de Revente (€/kWh)']:.4f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['ROI Moyen (%)']:.2f}%</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['TRI Moyen (%)']:.2f}%</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['VAN Moyenne (€)']:,.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['DSCR Moyen']:.2f}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{data['Probabilité Succès Global (%)']:.1f}%</td>
            </tr>
            """
        
        # Construire la section HTML
        html = f"""
        <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Résultats de la Simulation Monte Carlo</h2>
            
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background-color: #e74c3c; color: white;">
                            <th style="padding: 12px; text-align: left;">Scénario</th>
                            <th style="padding: 12px; text-align: right;">Prix de Revente (€/kWh)</th>
                            <th style="padding: 12px; text-align: right;">ROI Moyen (%)</th>
                            <th style="padding: 12px; text-align: right;">TRI Moyen (%)</th>
                            <th style="padding: 12px; text-align: right;">VAN Moyenne (€)</th>
                            <th style="padding: 12px; text-align: right;">DSCR Moyen</th>
                            <th style="padding: 12px; text-align: right;">Probabilité Succès Global (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background-color: #fadbd8; border-radius: 5px;">
                <h3 style="color: #e74c3c;">Analyse de Robustesse</h3>
                <p>Le scénario <strong>{monte_carlo_data[0]['Scénario']}</strong> présente la meilleure probabilité de succès global ({monte_carlo_data[0]['Probabilité Succès Global (%)']:.1f}%) avec un prix de revente de <strong>{monte_carlo_data[0]['Prix de Revente (€/kWh)']:.4f} €/kWh</strong>.</p>
                
                <p>Cette simulation montre que :</p>
                <ul>
                    <li>La probabilité d'obtenir un ROI supérieur à 5% est de {monte_carlo_data[0]['Probabilité ROI > 5% (%)']:.1f}%</li>
                    <li>La probabilité d'obtenir un TRI supérieur à 4% est de {monte_carlo_data[0]['Probabilité TRI > 4% (%)']:.1f}%</li>
                    <li>La probabilité d'obtenir un DSCR supérieur à 1.15 est de {monte_carlo_data[0]['Probabilité DSCR > 1.15 (%)']:.1f}%</li>
                </ul>
                
                <p>Conclusion sur la robustesse du projet : 
                """
        
        # Ajouter la conclusion en fonction de la probabilité de succès
        if monte_carlo_data[0]['Probabilité Succès Global (%)'] >= 90:
            html += "<strong style='color: green;'>Très robuste</strong>. Le projet présente une excellente résistance aux variations de production et de consommation."
        elif monte_carlo_data[0]['Probabilité Succès Global (%)'] >= 75:
            html += "<strong style='color: #2ecc71;'>Robuste</strong>. Le projet présente une bonne résistance aux variations de production et de consommation."
        elif monte_carlo_data[0]['Probabilité Succès Global (%)'] >= 50:
            html += "<strong style='color: orange;'>Modérément robuste</strong>. Le projet présente une résistance moyenne aux variations de production et de consommation."
        else:
            html += "<strong style='color: red;'>Peu robuste</strong>. Le projet est sensible aux variations de production et de consommation."
        
        html += """
                </p>
            </div>
        </div>
        """
        
        return html
    
    def create_conclusion_section(self):
        """
        Crée une section de conclusion
        
        Returns:
            str: HTML pour la section de conclusion
        """
        # Vérifier qu'il y a des résultats d'optimisation
        if not hasattr(st.session_state, 'optimization_results') or not st.session_state.optimization_results:
            return "<p>Impossible de générer une conclusion sans résultats d'optimisation.</p>"
        
        # Récupérer le meilleur scénario d'optimisation
        optimization_data = []
        for scenario_name, scenario_results in st.session_state.optimization_results.items():
            # Récupérer les indicateurs optimaux
            indicateurs = scenario_results['indicateurs_optimaux']
            scenario_data = {
                'Scénario': scenario_name,
                'Prix Optimal (€/kWh)': scenario_results['prix_optimal'],
                'ROI (%)': indicateurs['roi'] * 100,
                'TRI (%)': indicateurs['irr'] * 100 if indicateurs['irr'] is not None else 0,
                'VAN (€)': indicateurs['npv'],
                'Période de Récupération (ans)': indicateurs['payback_period'] if indicateurs['payback_period'] != float('inf') else 30,
                'DSCR moyen': indicateurs['avg_dscr'],
                'Score Global': indicateurs['scores']['score_global']
            }
            optimization_data.append(scenario_data)
        
        # Trier par score global décroissant
        optimization_data.sort(key=lambda x: x['Score Global'], reverse=True)
        best_scenario = optimization_data[0]
        
        # Vérifier si on a des résultats Monte Carlo pour ce scénario
        monte_carlo_probability = None
        if hasattr(st.session_state, 'monte_carlo_results') and st.session_state.monte_carlo_results:
            for scenario_name, scenario_results in st.session_state.monte_carlo_results.items():
                if scenario_name == best_scenario['Scénario']:
                    monte_carlo_probability = scenario_results['probabilities']['global'] * 100
                    break
        
        # Tarif EDF de référence
        tarif_edf = st.session_state.config['tarif_edf_reference']
        
        # Compétitivité par rapport à EDF
        if best_scenario['Prix Optimal (€/kWh)'] < tarif_edf:
            competitivite = f"<span style='color: green;'>compétitif</span> par rapport au tarif EDF ({tarif_edf:.4f} €/kWh) avec un avantage de {(tarif_edf - best_scenario['Prix Optimal (€/kWh)'])/tarif_edf*100:.1f}%"
        else:
            competitivite = f"<span style='color: red;'>non compétitif</span> par rapport au tarif EDF ({tarif_edf:.4f} €/kWh) avec un désavantage de {(best_scenario['Prix Optimal (€/kWh)'] - tarif_edf)/tarif_edf*100:.1f}%"
        
        # Construire la section HTML
        html = f"""
        <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px; margin-bottom: 20px;">
            <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Conclusion et Recommandation</h2>
            
            <div style="background-color: #d5f5e3; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #27ae60;">Recommandation Principale</h3>
                <p style="font-size: 18px;">Le prix de revente optimal recommandé est de <strong>{best_scenario['Prix Optimal (€/kWh)']:.4f} €/kWh</strong> selon le scénario <strong>{best_scenario['Scénario']}</strong>.</p>
                <p>Ce prix est {competitivite}.</p>
                
                <p>Avec ce prix, le projet présente :</p>
                <ul>
                    <li>Un ROI de <strong>{best_scenario['ROI (%)']:.2f}%</strong></li>
                    <li>Un TRI de <strong>{best_scenario['TRI (%)']:.2f}%</strong></li>
                    <li>Une VAN de <strong>{best_scenario['VAN (€)']:,.2f} €</strong></li>
                    <li>Une période de récupération de <strong>{best_scenario['Période de Récupération (ans)']:.1f} ans</strong></li>
                    <li>Un DSCR moyen de <strong>{best_scenario['DSCR moyen']:.2f}</strong></li>
                </ul>
                
                {f"<p>La simulation Monte Carlo montre une probabilité de succès global de <strong>{monte_carlo_probability:.1f}%</strong>.</p>" if monte_carlo_probability is not None else ""}
            </div>
            
            <div style="background-color: #ebf5fb; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: #2980b9;">Points d'Attention</h3>
                <ul>
                    <li>Vérifiez que les hypothèses du scénario recommandé sont réalistes et adaptées au contexte du projet.</li>
                    <li>Assurez-vous que le prix de revente est acceptable pour les acheteurs locaux potentiels.</li>
                    <li>Surveillez l'évolution du tarif EDF qui sert de référence pour la compétitivité.</li>
                    <li>Réalisez une étude de marché approfondie pour confirmer la demande locale d'électricité.</li>
                </ul>
            </div>
            
            <div style="background-color: #fef9e7; padding: 15px; border-radius: 5px;">
                <h3 style="color: #f39c12;">Étapes Suivantes</h3>
                <ol>
                    <li>Confirmez la faisabilité technique du projet avec les parties prenantes.</li>
                    <li>Présentez les résultats aux investisseurs potentiels.</li>
                    <li>Engagez des discussions avec les acheteurs locaux potentiels pour valider leur intérêt au prix recommandé.</li>
                    <li>Finalisez la structure de financement du projet.</li>
                    <li>Élaborez un plan de mise en œuvre détaillé.</li>
                </ol>
            </div>
        </div>
        """
        
        return html
    
    def generate_html_report(self, title, include_charts=True):
        """
        Génère un rapport HTML complet
        
        Args:
            title: Titre du rapport
            include_charts: Inclure les graphiques ou non
            
        Returns:
            str: HTML du rapport complet
        """
        # En-tête HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #3498db;
                    margin-bottom: 30px;
                }}
                h2 {{
                    color: #2980b9;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }}
                .header {{
                    background-color: #3498db;
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    text-align: center;
                    font-size: 0.9em;
                    color: #777;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
        """
        
        # Ajouter les sections
        html += self.create_summary_section()
        
        # Ajouter les graphiques si demandé
        if include_charts:
            html += """
            <div style="padding: 20px; background-color: #f5f5f5; border-radius: 10px; margin-bottom: 20px;">
                <h2 style="color: #2c3e50; text-align: center; margin-bottom: 20px;">Visualisations</h2>
                <p style="text-align: center; color: #777;">Les graphiques ne peuvent pas être intégrés directement dans le rapport HTML. Veuillez consulter l'onglet Visualisation de l'application pour les voir.</p>
            </div>
            """
        
        # Ajouter la section d'optimisation
        html += self.create_optimization_section()
        
        # Ajouter la section Monte Carlo
        html += self.create_monte_carlo_section()
        
        # Ajouter la conclusion
        html += self.create_conclusion_section()
        
        # Pied de page
        html += """
            <div class="footer">
                <p>Rapport généré par OptimPV - Application d'optimisation de l'autoconsommation collective</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def show_ui(self):
        """Affiche l'interface utilisateur du module de reporting"""
        st.markdown("<h1 class='main-header'>Rapports</h1>", unsafe_allow_html=True)
        
        # Vérifier que les données nécessaires sont disponibles
        if not st.session_state.data_imported:
            st.warning("Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'onglet 'Importation Données'.")
            return
        
        # Créer des onglets pour les différents types de rapports
        tab1, tab2, tab3 = st.tabs(["Rapport Complet", "Rapports Spécifiques", "Exportation"])
        
        with tab1:
            st.markdown("<h3 class='sub-header'>Génération d'un Rapport Complet</h3>", unsafe_allow_html=True)
            
            st.markdown("""
            Cette section vous permet de générer un rapport complet incluant :
            - Un résumé du projet (contexte, configuration)
            - Les résultats d'optimisation du prix de revente
            - Les résultats de la simulation Monte Carlo
            - Une conclusion et des recommandations
            
            Le rapport peut être généré au format HTML ou PDF.
            """)
            
            # Options du rapport
            col1, col2 = st.columns(2)
            
            with col1:
                report_title = st.text_input(
                    "Titre du rapport",
                    value=f"Rapport d'Optimisation de l'Autoconsommation Collective - {datetime.now().strftime('%d/%m/%Y')}",
                    key="report_title"
                )
                
                report_format = st.selectbox(
                    "Format du rapport",
                    options=["HTML", "PDF"],
                    index=0,
                    key="report_format"
                )
            
            with col2:
                include_summary = st.checkbox("Inclure le résumé du projet", value=True, key="include_summary")
                include_optimization = st.checkbox("Inclure les résultats d'optimisation", value=True, key="include_optimization")
                include_monte_carlo = st.checkbox("Inclure les résultats Monte Carlo", value=True, key="include_monte_carlo")
                include_charts = st.checkbox("Inclure les graphiques", value=True, key="include_charts")
            
            # Bouton pour générer le rapport
            if st.button("Générer le rapport complet", key="generate_full_report"):
                with st.spinner("Génération du rapport en cours..."):
                    # Générer le rapport HTML
                    html_report = self.generate_html_report(report_title, include_charts)
                    
                    # Enregistrer le rapport dans la session
                    report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state.reports[report_id] = {
                        'title': report_title,
                        'format': report_format,
                        'html': html_report,
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Proposer le téléchargement
                    if report_format == "HTML":
                        # Créer un bouton de téléchargement pour HTML
                        st.download_button(
                            label="Télécharger le rapport HTML",
                            data=html_report,
                            file_name=f"rapport_{report_id}.html",
                            mime="text/html"
                        )
                    else:
                        # Pour PDF, on devrait convertir le HTML en PDF
                        # Mais comme cela nécessite des dépendances externes,
                        # on peut proposer de télécharger le HTML à la place
                        st.warning("La conversion en PDF nécessite des bibliothèques supplémentaires. Le rapport est disponible au format HTML à la place.")
                        st.download_button(
                            label="Télécharger le rapport HTML",
                            data=html_report,
                            file_name=f"rapport_{report_id}.html",
                            mime="text/html"
                        )
                    
                    # Afficher un aperçu
                    st.markdown("<h4>Aperçu du rapport</h4>", unsafe_allow_html=True)
                    st.components.v1.html(html_report, height=600, scrolling=True)
        
        with tab2:
            st.markdown("<h3 class='sub-header'>Rapports Spécifiques</h3>", unsafe_allow_html=True)
            
            # Sélection du type de rapport
            report_type = st.selectbox(
                "Type de rapport",
                options=["Résumé du Projet", "Analyse Économique", "Résultats d'Optimisation", "Analyse Monte Carlo"],
                index=0,
                key="specific_report_type"
            )
            
            # Options selon le type de rapport
            if report_type == "Résumé du Projet":
                # Pas d'options spécifiques pour le résumé
                st.info("Ce rapport contient un résumé des paramètres du projet et des statistiques énergétiques de base.")
                
                if st.button("Générer le rapport de résumé", key="generate_summary_report"):
                    # Générer le résumé
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <title>Résumé du Projet</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                line-height: 1.6;
                                color: #333;
                                max-width: 1200px;
                                margin: 0 auto;
                                padding: 20px;
                            }}
                            h1 {{
                                color: #2c3e50;
                                text-align: center;
                                padding-bottom: 10px;
                                border-bottom: 2px solid #3498db;
                                margin-bottom: 30px;
                            }}
                        </style>
                    </head>
                    <body>
                        <h1>Résumé du Projet</h1>
                        {self.create_summary_section()}
                    </body>
                    </html>
                    """
                    
                    # Proposer le téléchargement
                    st.download_button(
                        label="Télécharger le rapport de résumé",
                        data=html_content,
                        file_name=f"resume_projet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html"
                    )
                    
                    # Afficher un aperçu
                    st.markdown("<h4>Aperçu du rapport</h4>", unsafe_allow_html=True)
                    st.components.v1.html(html_content, height=600, scrolling=True)
            
            elif report_type == "Analyse Économique":
                # Sélection du scénario
                scenarios = []
                if hasattr(st.session_state, 'economic_results') and st.session_state.economic_results:
                    scenarios = list(st.session_state.economic_results.keys())
                
                if not scenarios:
                    st.warning("Aucun résultat d'analyse économique disponible. Veuillez d'abord calculer les indicateurs économiques.")
                else:
                    selected_scenario = st.selectbox(
                        "Scénario à analyser",
                        options=scenarios,
                        index=0,
                        key="economic_report_scenario"
                    )
                    
                    if st.button("Générer le rapport d'analyse économique", key="generate_economic_report"):
                        # Récupérer les résultats pour ce scénario
                        results = st.session_state.economic_results[selected_scenario]
                        
                        # Créer un DataFrame pour les flux financiers
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
                        
                        # Créer le tableau HTML
                        table_html = "<table style='width:100%; border-collapse: collapse;'>"
                        
                        # En-tête du tableau
                        table_html += "<thead><tr style='background-color: #3498db; color: white;'>"
                        for col in df_financial.columns:
                            table_html += f"<th style='padding: 10px; text-align: left;'>{col}</th>"
                        table_html += "</tr></thead>"
                        
                        # Corps du tableau
                        table_html += "<tbody>"
                        for _, row in df_financial.iterrows():
                            table_html += "<tr style='border-bottom: 1px solid #ddd;'>"
                            for i, col in enumerate(df_financial.columns):
                                if i == 0:  # Année
                                    table_html += f"<td style='padding: 10px;'>{row[col]}</td>"
                                else:  # Valeurs numériques
                                    table_html += f"<td style='padding: 10px; text-align: right;'>{row[col]:,.2f}</td>"
                            table_html += "</tr>"
                        table_html += "</tbody></table>"
                        
                        # Générer le contenu HTML
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <title>Analyse Économique - Scénario {selected_scenario}</title>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    max-width: 1200px;
                                    margin: 0 auto;
                                    padding: 20px;
                                }}
                                h1, h2 {{
                                    color: #2c3e50;
                                    padding-bottom: 10px;
                                    border-bottom: 2px solid #3498db;
                                    margin-bottom: 20px;
                                }}
                                .indicator-card {{
                                    background-color: #f8f9fa;
                                    border-radius: 5px;
                                    padding: 15px;
                                    margin-bottom: 20px;
                                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                                }}
                                .indicator-card h3 {{
                                    margin-top: 0;
                                    color: #3498db;
                                }}
                                .indicator-value {{
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: #2c3e50;
                                }}
                                .indicator-grid {{
                                    display: grid;
                                    grid-template-columns: repeat(3, 1fr);
                                    gap: 15px;
                                }}
                                table {{
                                    width: 100%;
                                    border-collapse: collapse;
                                    margin: 20px 0;
                                }}
                                th, td {{
                                    padding: 10px;
                                    border-bottom: 1px solid #ddd;
                                }}
                                th {{
                                    background-color: #3498db;
                                    color: white;
                                    text-align: left;
                                }}
                            </style>
                        </head>
                        <body>
                            <h1>Analyse Économique - Scénario {selected_scenario}</h1>
                            
                            <div class="indicator-grid">
                                <div class="indicator-card">
                                    <h3>ROI</h3>
                                    <div class="indicator-value">{results['roi']*100:.2f}%</div>
                                </div>
                                
                                <div class="indicator-card">
                                    <h3>TRI (IRR)</h3>
                                    <div class="indicator-value">{results['irr']*100:.2f}%</div>
                                </div>
                                
                                <div class="indicator-card">
                                    <h3>VAN (NPV)</h3>
                                    <div class="indicator-value">{results['npv']:,.2f} €</div>
                                </div>
                                
                                <div class="indicator-card">
                                    <h3>Période de Récupération</h3>
                                    <div class="indicator-value">{results['payback_period']:.2f} ans</div>
                                </div>
                                
                                <div class="indicator-card">
                                    <h3>DSCR moyen</h3>
                                    <div class="indicator-value">{results['avg_dscr']:.2f}</div>
                                </div>
                                
                                <div class="indicator-card">
                                    <h3>Prix de Revente</h3>
                                    <div class="indicator-value">{results['prix_revente']:.4f} €/kWh</div>
                                </div>
                            </div>
                            
                            <h2>Flux Financiers</h2>
                            {table_html}
                            
                            <div style="margin-top: 30px; padding: 15px; background-color: #e8f4f8; border-radius: 5px;">
                                <h3 style="color: #3498db; margin-top: 0;">Interprétation</h3>
                                <p>L'analyse économique du scénario <strong>{selected_scenario}</strong> montre :</p>
                                <ul>
                                    <li>Un ROI de {results['roi']*100:.2f}%, ce qui {' est satisfaisant' if results['roi'] >= 0.05 else ' est insuffisant'}.</li>
                                    <li>Un TRI de {results['irr']*100:.2f}%, ce qui {' est satisfaisant' if results['irr'] is not None and results['irr'] >= 0.04 else ' est insuffisant'}.</li>
                                    <li>Une VAN de {results['npv']:,.2f} €, ce qui {' est positive et indique une création de valeur' if results['npv'] > 0 else ' est négative et indique une destruction de valeur'}.</li>
                                    <li>Une période de récupération de {results['payback_period']:.2f} ans, ce qui {' est satisfaisant' if results['payback_period'] <= 15 else ' est trop long'}.</li>
                                    <li>Un DSCR moyen de {results['avg_dscr']:.2f}, ce qui {' est suffisant pour couvrir le service de la dette' if results['avg_dscr'] >= st.session_state.config['target_dscr'] else ' est insuffisant pour couvrir le service de la dette'}.</li>
                                </ul>
                            </div>
                        </body>
                        </html>
                        """
                        
                        # Proposer le téléchargement
                        st.download_button(
                            label="Télécharger le rapport d'analyse économique",
                            data=html_content,
                            file_name=f"analyse_economique_{selected_scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html"
                        )
                        
                        # Afficher un aperçu
                        st.markdown("<h4>Aperçu du rapport</h4>", unsafe_allow_html=True)
                        st.components.v1.html(html_content, height=600, scrolling=True)
            
            elif report_type == "Résultats d'Optimisation":
                if not hasattr(st.session_state, 'optimization_results') or not st.session_state.optimization_results:
                    st.warning("Aucun résultat d'optimisation disponible. Veuillez d'abord effectuer une optimisation.")
                else:
                    if st.button("Générer le rapport des résultats d'optimisation", key="generate_optimization_report"):
                        # Générer le contenu HTML
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <title>Résultats d'Optimisation</title>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    max-width: 1200px;
                                    margin: 0 auto;
                                    padding: 20px;
                                }}
                                h1, h2 {{
                                    color: #2c3e50;
                                    padding-bottom: 10px;
                                    border-bottom: 2px solid #3498db;
                                    margin-bottom: 20px;
                                }}
                            </style>
                        </head>
                        <body>
                            <h1>Résultats d'Optimisation du Prix de Revente</h1>
                            {self.create_optimization_section()}
                        </body>
                        </html>
                        """
                        
                        # Proposer le téléchargement
                        st.download_button(
                            label="Télécharger le rapport d'optimisation",
                            data=html_content,
                            file_name=f"resultats_optimisation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html"
                        )
                        
                        # Afficher un aperçu
                        st.markdown("<h4>Aperçu du rapport</h4>", unsafe_allow_html=True)
                        st.components.v1.html(html_content, height=600, scrolling=True)
            
            elif report_type == "Analyse Monte Carlo":
                if not hasattr(st.session_state, 'monte_carlo_results') or not st.session_state.monte_carlo_results:
                    st.warning("Aucun résultat de simulation Monte Carlo disponible. Veuillez d'abord effectuer une simulation.")
                else:
                    if st.button("Générer le rapport d'analyse Monte Carlo", key="generate_monte_carlo_report"):
                        # Générer le contenu HTML
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <title>Analyse Monte Carlo</title>
                            <style>
                                body {{
                                    font-family: Arial, sans-serif;
                                    line-height: 1.6;
                                    color: #333;
                                    max-width: 1200px;
                                    margin: 0 auto;
                                    padding: 20px;
                                }}
                                h1, h2 {{
                                    color: #2c3e50;
                                    padding-bottom: 10px;
                                    border-bottom: 2px solid #3498db;
                                    margin-bottom: 20px;
                                }}
                            </style>
                        </head>
                        <body>
                            <h1>Analyse de Robustesse - Simulation Monte Carlo</h1>
                            {self.create_monte_carlo_section()}
                        </body>
                        </html>
                        """
                        
                        # Proposer le téléchargement
                        st.download_button(
                            label="Télécharger le rapport d'analyse Monte Carlo",
                            data=html_content,
                            file_name=f"analyse_monte_carlo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                            mime="text/html"
                        )
                        
                        # Afficher un aperçu
                        st.markdown("<h4>Aperçu du rapport</h4>", unsafe_allow_html=True)
                        st.components.v1.html(html_content, height=600, scrolling=True)
        
        with tab3:
            st.markdown("<h3 class='sub-header'>Exportation des Rapports</h3>", unsafe_allow_html=True)
            
            # Afficher les rapports existants
            if not st.session_state.reports:
                st.info("Aucun rapport n'a été généré. Veuillez d'abord générer un rapport.")
            else:
                st.markdown("### Rapports Générés")
                
                # Créer un tableau des rapports
                reports_data = []
                for report_id, report in st.session_state.reports.items():
                    reports_data.append({
                        "ID": report_id,
                        "Titre": report['title'],
                        "Format": report['format'],
                        "Date": report['date']
                    })
                
                df_reports = pd.DataFrame(reports_data)
                
                # Afficher le tableau
                st.dataframe(df_reports, use_container_width=True)
                
                # Sélectionner un rapport à exporter
                selected_report_id = st.selectbox(
                    "Sélectionner un rapport à exporter",
                    options=df_reports["ID"].tolist(),
                    format_func=lambda x: f"{df_reports[df_reports['ID'] == x]['Titre'].iloc[0]} ({x})",
                    key="export_report_id"
                )
                
                if st.button("Exporter le rapport sélectionné", key="export_selected_report"):
                    # Récupérer le rapport
                    report = st.session_state.reports[selected_report_id]
                    
                    # Proposer le téléchargement
                    st.download_button(
                        label=f"Télécharger {report['title']}",
                        data=report['html'],
                        file_name=f"rapport_{selected_report_id}.html",
                        mime="text/html"
                    )


def format_value(value, unit='€', decimals=0, default_na="N/A"):
    """Formate une valeur numérique avec unité et décimales, gère NaN/None/Inf."""
    if pd.isna(value) or value is None or not np.isfinite(value):
        if isinstance(value, float) and np.isinf(value) and unit is None :
             return "+∞" # Symbole infini
        return default_na
    try:
        if unit == '%':
            format_str = f"{{:,.{decimals}f}}%"
            return format_str.format(value)
        format_str = f"{{:,.{decimals}f}}"
        formatted_value = format_str.format(value)
        if unit is None or unit == "": return formatted_value
        elif unit == '€': return f"{formatted_value} €"
        elif unit == 'kWh': return f"{formatted_value} kWh"
        else: return f"{formatted_value} {unit}"
    except (ValueError, TypeError):
        return str(value)

# --- NOUVELLE FONCTION ---
def generate_detailed_excel_report(results: dict, config: dict) -> io.BytesIO:
    """
    Génère un fichier Excel multi-feuilles détaillé pour analyse financière.

    Args:
        results: Dictionnaire contenant les résultats de l'analyse
                 (doit inclure 'monthly_data' et les KPIs globaux).
        config: Dictionnaire de configuration utilisé pour la simulation.

    Returns:
        Un objet BytesIO contenant le fichier Excel.
    """
    if not results or not isinstance(results, dict):
        raise ValueError("Le dictionnaire 'results' est invalide ou vide.")
    if not config or not isinstance(config, dict):
        raise ValueError("Le dictionnaire 'config' est invalide ou vide.")

    monthly_data = results.get('monthly_data')
    if not isinstance(monthly_data, pd.DataFrame):
         raise ValueError("Les données mensuelles ('monthly_data') sont manquantes ou invalides dans les résultats.")

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        # --- Feuille 1: Paramètres & Hypothèses ---
        params_data = []
        # Sélectionner et formater les paramètres clés (liste à compléter/ajuster)
        params_to_include = {
            "scenario": "Nom Scénario Utilisé",
            "prix_revente": "Prix de Vente Optimal Testé (€/kWh)",
            "puissance_kwc": "Puissance (kWc)",
            "capex": "CAPEX Scénario (€)",
            "total_subvention": "Subvention Totale Calculée (€)",
            # Calculer CAPEX Net ici pour info
            "opex_method": "Méthode OPEX",
            "opex": "OPEX Annuel Final (€/an)",
            "opex_onduleur_provision": "Provision Onduleur Incluse?",
            "turpe_prod_calculee": "TURPE Annuel Base (€/an - Calculé)",
            "turpe_indexe_inflation": "Indexation TURPE sur Inflation Générale?",
            "taux_inflation": "Taux Inflation Général (%)",
            "taux_imposition": "Taux Imposition (%)",
            "cout_fonds_propres": "Coût Fonds Propres (%)",
            "with_loan": "Financement par Prêt?",
            "debt_ratio": "Ratio Dette/Total (%)",
            "taux_interet_dette": "Taux Intérêt Dette (%)",
            "debt_term_years": "Durée Prêt (ans)",
            "target_dscr": "DSCR Cible",
            "duree_ppa": "Durée Simulation (mois)",
            "date_debut_ppa": "Date Début PPA",
            "duree_construction": "Durée Construction (mois)",
            "degradation_rate": "Taux Dégradation Annuel (%)",
            "tarif_oa": "Tarif OA (€/kWh)",
            "tarif_oa_indexe_inflation": "Indexation Tarif OA?",
            "taux_inflation_tarif_oa": "Taux Inflation Spécifique OA (%)",
            "tarif_edf_reference": "Tarif EDF Référence (€/kWh)",
            "source_prix_autoconso": "Source Valorisation Autoconsommation",
            "amortissement_duree": "Durée Amortissement Comptable (ans)",
            "valeur_residuelle_pct": "Valeur Résiduelle (%)",
            "cout_demantelement_pct": "Coût Démantèlement (%)",
            "shl_blocage_period": "Blocage Remb. SHL (mois)",
            "dividends_blocage_period": "Blocage Dividendes (mois)",
        }

        # Ajouter le CAPEX Net
        capex_res = results.get('capex', 0)
        sub_res = results.get('total_subvention', 0)
        params_data.append({"Paramètre": "CAPEX Net de Subvention (€)", "Valeur": format_value(max(0, capex_res - sub_res), '€', 0)})

        for key, display_name in params_to_include.items():
            value = results.get(key) # Essayer d'abord dans results (contient config + kpis)
            if value is None:
                 value = config.get(key) # Sinon chercher dans config

            formatted_value = str(value) # Fallback
            if isinstance(value, (int, float, np.number)):
                if "€" in display_name: formatted_value = format_value(value, '€', 0 if value > 1000 else 2)
                elif "%" in display_name: formatted_value = format_value(value, '%', 1)
                elif "/kWh" in display_name: formatted_value = format_value(value, '€/kWh', 4)
                elif "(ans)" in display_name: formatted_value = format_value(value, '', 1)
                elif "(mois)" in display_name: formatted_value = str(int(value))
                elif "kWc" in display_name: formatted_value = format_value(value, 'kWc', 1)
                elif "Ratio" in display_name or "DSCR" in display_name: formatted_value = format_value(value, '', 2)
                else: formatted_value = format_value(value, '', 2)
            elif isinstance(value, bool):
                formatted_value = "Oui" if value else "Non"

            params_data.append({"Paramètre": display_name, "Valeur": formatted_value})

        df_params = pd.DataFrame(params_data)
        df_params.to_excel(writer, sheet_name='Parametres_Cles', index=False)
        # Ajuster largeur colonnes
        worksheet = writer.sheets['Parametres_Cles']
        worksheet.set_column('A:A', 45) # Colonne Paramètre plus large
        worksheet.set_column('B:B', 25) # Colonne Valeur

        # --- Feuille 2: Logique de Calcul ---
        logic_data = [
            {"Indicateur": "Production Annuelle", "Logique": "Issue des données de production importées (PVGIS, etc.)"},
            {"Indicateur": "Consommation Annuelle", "Logique": "Issue des données de consommation importées ou profil type"},
            {"Indicateur": "Autoconsommation", "Logique": "Min(Production, Consommation) à chaque pas de temps (horaire)"},
            {"Indicateur": "Vente Surplus", "Logique": "Max(0, Production - Consommation)"},
            {"Indicateur": "Achat Réseau", "Logique": "Max(0, Consommation - Production)"},
            {"Indicateur": "Revenus Vente Surplus", "Logique": "Vente Surplus * Prix Achat Surplus (OA Solaire)"},
            {"Indicateur": "Revenus Vente Autoconso", "Logique": "Autoconsommation * Prix de Vente Client (Optimisé ou Fixé)"},
            {"Indicateur": "Économies sur Facture (Client)", "Logique": "Autoconsommation * (Tarif EDF Référence - Prix Vente Client)"},
            {"Indicateur": "Revenus Totaux", "Logique": "Revenus Vente Surplus + Revenus Vente Autoconso + Prime Autoconso"},
            {"Indicateur": "OPEX", "Logique": "Somme des coûts opérationnels annuels (Maintenance, Assurance, Comptabilité, etc.)"},
            {"Indicateur": "TURPE", "Logique": "Calculé selon règles CRE (terme fixe + terme variable sur énergie soutirée)"},
            {"Indicateur": "EBITDA", "Logique": "Revenus Totaux - OPEX - TURPE"},
            {"Indicateur": "Amortissement", "Logique": "Base Amortissable (CAPEX - Subvention) / Durée Amortissement"},
            {"Indicateur": "EBIT", "Logique": "EBITDA - Amortissement"},
            {"Indicateur": "Intérêts", "Logique": "Solde Dette Début Période * Taux d'Intérêt Annuel"},
            {"Indicateur": "EBT", "Logique": "EBIT - Intérêts"},
            {"Indicateur": "Impôts Provisionnés", "Logique": "Max(0, EBT * Taux d'Imposition)"},
            {"Indicateur": "Résultat Net", "Logique": "EBT - Impôts Provisionnés"},
            {"Indicateur": "Principal Remboursé", "Logique": "Service Dette - Intérêts (calculé selon type d'échéancier)"},
            {"Indicateur": "Variation BFR", "Logique": "Généralement nul ou faible impact pour ce type de projet"},
            {"Indicateur": "OCF Projet (FCF)", "Logique": "EBITDA * (1 - Taux IS) + Amortissement * Taux IS - Inv"},
            {"Indicateur": "Free Cash Flow Equity (FCFE)", "Logique": "Résultat Net + Amortissement - Principal Remboursé (+/- Variation Dette)"},
            {"Indicateur": "Service Dette", "Logique": "Principal + Intérêts"},
            {"Indicateur": "DSCR", "Logique": "(EBITDA - Impôts Prov.) / Service Dette"},
            {"Indicateur": "VAN", "Logique": "Somme(Flux Actualisés) - Invest. Initial (Taux/Flux spécifiques Projet/Equity)"},
            {"Indicateur": "TRI", "Logique": "Taux Annuel équivalent rendant VAN = 0 (Flux spécifiques Projet/Equity)"},
            {"Indicateur": "LCOE", "Logique": "-VAN(Coûts) / VAN(Production), actualisé au WACC"},
            {"Indicateur": "Payback", "Logique": "Temps (années) pour Flux Cumulés >= Invest. Initial (Flux spécifiques Projet/Equity)"},

            # --- AJOUTER CETTE ENTRÉE ---
            {
                "Indicateur": "Prix de Vente Optimal",
                "Logique": f"Recherche itérative (via scipy.optimize.minimize/brentq) du prix initial maximisant la VAN Fonds Propres, sous contraintes: TRI Projet >= {config.get('constraint_min_project_irr_pct', 'N/A')}%, Payback Equity <= {config.get('constraint_max_payback', 'N/A')} ans, Gain Client >= {config.get('constraint_min_consumer_gain_pct', 'N/A')}% vs Tarif EDF Réf ({config.get('tarif_edf_reference', 'N/A')} €/kWh)."
            },
            # --- FIN DE L'AJOUT ---
        ]
        df_logic = pd.DataFrame(logic_data)
        df_logic.to_excel(writer, sheet_name='Logique_Calcul', index=False)
        worksheet_logic = writer.sheets['Logique_Calcul']
        worksheet_logic.set_column('A:A', 30)
        worksheet_logic.set_column('B:B', 80) # Colonne Logique large

        # --- Feuille 3: Données Mensuelles Détaillées ---
        if monthly_data is not None and not monthly_data.empty:
            # S'assurer que l'index est bien la date si ce n'est pas le cas
            if not isinstance(monthly_data.index, pd.DatetimeIndex):
                 monthly_data_export = monthly_data.set_index('Temps') if 'Temps' in monthly_data.columns else monthly_data
            else:
                 monthly_data_export = monthly_data
            monthly_data_export.to_excel(writer, sheet_name='Flux_Mensuels')
            worksheet_monthly = writer.sheets['Flux_Mensuels']
            worksheet_monthly.set_column('A:A', 18) # Colonne Date
            # Ajuster autres colonnes si besoin (peut être lent si bcp de colonnes)
            for i, col in enumerate(monthly_data_export.columns):
                 worksheet_monthly.set_column(i + 1, i + 1, 15)

        # --- Feuille 4: Synthèse Annuelle (Placeholder - Nécessite le code de pivot) ---
        # Pour l'instant, on met un message. Il faudrait intégrer ici la logique
        # de pivot et de calcul des totaux annuels de financial_summary_table.py
        # C'est la partie la plus complexe à ajouter ici.
        df_annual_placeholder = pd.DataFrame({"Info": ["La logique de génération du tableau annuel détaillé doit être implémentée ici."]})
        df_annual_placeholder.to_excel(writer, sheet_name='Synthese_Annuelle', index=False)

        # --- Feuille 5: KPIs Globaux ---
        kpi_data = []
        kpis_to_include = [
            ('VAN Projet (€)', 'npv_project', '€', 0),
            ('TRI Projet (%)', 'irr_project', '%', 1),
            ('Payback Projet (ans)', 'payback_project', '', 1),
            ('LCOE (€/kWh)', 'lcoe', '€/kWh', 4),
            ('VAN Equity (€)', 'npv', '€', 0), # Utilise 'npv' pour equity NPV
            ('TRI Equity (%)', 'irr', '%', 1),   # Utilise 'irr' pour equity IRR
            ('Payback Equity (ans)', 'payback_period', '', 1), # Utilise 'payback_period'
            ('DSCR Moyen', 'avg_dscr', '', 2),
            # Ajouter LLCR/PLCR ici quand ils seront calculés
            ('Taux Autoconso Moyen (%)', 'autoconsumption_rate', '%', 1),
            ('Taux Autoprod Moyen (%)', 'autoproduction_rate', '%', 1),
            # Ajouter des totaux agrégés si pertinent
            # ('Production Totale (kWh)', 'Total_Production_kWh', 'kWh', 0), # Nécessiterait de calculer ces totaux
        ]

        for display_name, key, unit, decimals in kpis_to_include:
            value = results.get(key)
            # Ajustement pour TRI/Taux qui sont en décimal mais affichés en %
            if unit == '%':
                 value = value * 100 if value is not None else None
            kpi_data.append({
                "Indicateur Clé Global": display_name,
                "Valeur": format_value(value, unit, decimals, default_na="-")
            })

        df_kpis = pd.DataFrame(kpi_data)
        df_kpis.to_excel(writer, sheet_name='KPIs_Globaux', index=False)
        worksheet_kpis = writer.sheets['KPIs_Globaux']
        worksheet_kpis.set_column('A:A', 35)
        worksheet_kpis.set_column('B:B', 20)

        # Le writer sauvegarde automatiquement le buffer à la sortie du 'with'

    buffer.seek(0)
    return buffer

# --- FIN DE LA NOUVELLE FONCTION ---

# Votre classe ReportingModule existante continue ici...
class ReportingModule:
    def __init__(self):
        # Initialiser les structures de données si elles n'existent pas
        if 'reports' not in st.session_state:
            st.session_state.reports = {}

    # ... (vos autres méthodes create_summary_section, etc. restent ici) ...
    # ... (assurez-vous que generate_html_report est toujours là si vous l'utilisez) ...

    def show_ui(self):
        """Affiche l'interface utilisateur du module de reporting"""
        st.markdown("<h1 class='main-header'>Rapports</h1>", unsafe_allow_html=True)

        # Vérifier que les données nécessaires sont disponibles
        # S'assurer que les résultats de l'optimisation contenant les indicateurs sont là
        if 'constrained_optim_results' not in st.session_state or not st.session_state.constrained_optim_results:
             st.warning("Aucun résultat d'optimisation disponible. Veuillez d'abord lancer l'optimisation dans l'onglet 'Analyse & Visualisation'.")
             return

        # Trouver le premier scénario ayant des résultats (pour l'export)
        target_scenario = None
        results_to_export = None
        config_to_export = st.session_state.get('config') # Config globale
        # Essayer de trouver le scénario actif ou le premier scénario optimisé
        for scenario_name, optim_data in st.session_state.constrained_optim_results.items():
             if isinstance(optim_data, dict) and 'indicateurs_au_prix_optimal' in optim_data:
                  target_scenario = scenario_name
                  results_to_export = optim_data['indicateurs_au_prix_optimal']
                  # On pourrait aussi vouloir passer la config spécifique au scénario si elle existe
                  # ou les modificateurs du scénario. Pour l'instant on passe la config globale.
                  break # Prendre le premier trouvé

        if results_to_export is None or config_to_export is None:
             st.warning("Les données nécessaires pour l'export (résultats financiers et configuration) n'ont pas pu être trouvées.")
             return


        # Créer des onglets pour les différents types de rapports
        tab1, tab2, tab3 = st.tabs(["Rapport Complet HTML", "Export Excel Détaillé", "Autres Exports"])

        # --- Onglet 1: Rapport HTML (inchangé pour l'instant) ---
        with tab1:
            st.markdown("<h3 class='sub-header'>Génération d'un Rapport Complet HTML</h3>", unsafe_allow_html=True)
            st.info("Génère un rapport HTML simple (ne contient pas tous les détails du nouvel export Excel).")
            # ... (garder votre logique de génération HTML ici si besoin) ...
            if st.button("Générer Rapport HTML (Exemple)", key="generate_html_report_btn"):
                 st.warning("La génération de rapport HTML n'est pas entièrement implémentée dans cet exemple.")


        # --- Onglet 2: Nouvel Export Excel Détaillé ---
        with tab2:
            st.markdown("<h3 class='sub-header'>Export Excel Détaillé pour Analyse</h3>", unsafe_allow_html=True)
            st.markdown("""
                Génère un fichier Excel multi-feuilles contenant :
                - Les paramètres clés utilisés pour la simulation.
                - Une description de la logique de calcul des indicateurs.
                - Les flux financiers mensuels détaillés.
                - La synthèse annuelle formatée.
                - Le récapitulatif des KPIs globaux.
            """)
            st.info(f"L'export sera basé sur les résultats du scénario : **{target_scenario}**")

            excel_filename = f"Analyse_Financiere_Detaillee_{target_scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            if st.button("Générer et Télécharger l'Export Excel Détaillé", key="generate_detailed_excel"):
                try:
                    with st.spinner("Génération du fichier Excel détaillé..."):
                        # Ajouter la config aux résultats pour la passer facilement
                        results_to_export['config_used_for_run'] = config_to_export
                        results_to_export['scenario_name'] = target_scenario # Assurer que le nom est là

                        excel_data = generate_detailed_excel_report(results_to_export, config_to_export)

                    st.success("Fichier Excel généré !")
                    st.download_button(
                        label="📥 Télécharger le Fichier Excel",
                        data=excel_data,
                        file_name=excel_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except ValueError as ve:
                    st.error(f"Erreur lors de la préparation des données pour l'export : {ve}")
                except Exception as e:
                    st.error(f"Erreur inattendue lors de la génération de l'export Excel : {e}")
                    st.exception(traceback.format_exc())


        # --- Onglet 3: Autres Exports (Garder l'ancien export simple si besoin) ---
        with tab3:
            st.markdown("<h3 class='sub-header'>Autres Options d'Export</h3>", unsafe_allow_html=True)
            st.info("Vous pouvez ajouter ici l'ancien export simple du tableau annuel si vous souhaitez le conserver.")
            # ... (Remettre ici la logique d'export simple de financial_summary_table si besoin) ...