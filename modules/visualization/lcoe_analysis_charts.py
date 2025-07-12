# Fichier: modules/visualization/lcoe_analysis_charts.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import copy
import traceback

try:
    # Assurez-vous que AnalysisEngine et aggregate_energy_data sont au bon endroit
    # par rapport à ce fichier (modules/visualization/)
    # Si ce fichier est dans modules/visualization/ et que engine_module est dans modules/
    # l'import devrait être : from ..engine_module.core_analyzer import AnalysisEngine
    from ..engine_module.core_analyzer import AnalysisEngine
    from ..engine_module.data_processing import aggregate_energy_data
except ImportError:
    st.error("ERREUR CRITIQUE: Impossible d'importer AnalysisEngine ou aggregate_energy_data dans lcoe_analysis_charts.py")
    # Définition de classes factices pour permettre à l'application de se charger partiellement en cas d'erreur d'import
    class AnalysisEngine:
        def __init__(self, *args, **kwargs):
            self.sites_data = {}
            st.warning("Utilisation d'une instance factice de AnalysisEngine.")
        def calculate_financial_indicators(self, *args, **kwargs):
            st.warning("Appel à calculate_financial_indicators sur une instance factice de AnalysisEngine.")
            return {"error": "Moteur d'analyse factice utilisé", "lcoe": np.nan}
    def aggregate_energy_data(*args, **kwargs):
        st.warning("Appel à aggregate_energy_data factice.")
        return pd.DataFrame(columns=['Temps', 'production_kwh', 'consumption_kwh'])

def simulate_lcoe_for_project_sizes(
    reference_profile_df: pd.DataFrame,
    power_of_reference_profile: float,
    base_config_global: dict,
    base_scenarios_dict: dict,
    target_scenario_name_sim: str,
    project_sizes_kwc_list: list,
    capex_input_type='per_kwc',
    capex_value=1000,
    opex_assumptions_sim=None,
    prix_vente_moyen_estime_pour_sim: float = None
):
    results_list_lcoe = []
    sim_config_global_lcoe = copy.deepcopy(base_config_global)

    if reference_profile_df is None or reference_profile_df.empty or power_of_reference_profile <= 0:
        st.warning("Profil de référence (agrégé du projet actuel) est invalide ou sa puissance est nulle. Analyse LCOE par taille annulée.")
        return pd.DataFrame(results_list_lcoe)

    for size_kwc_iter in project_sizes_kwc_list:
        current_iter_sites_config_dict = {}
        current_iter_sites_data_dict = {}
        temp_site_id = f"projet_simule_{size_kwc_iter}kWc"

        # 1. Déterminer CAPEX pour la taille simulée
        current_capex_val = 0.0
        if capex_input_type == 'per_kwc':
            current_capex_val = size_kwc_iter * float(capex_value)
        elif capex_input_type == 'total_map' and isinstance(capex_value, dict) and capex_value:
            # Logique pour trouver la clé la plus proche dans la map CAPEX
            available_sizes_in_map = sorted(list(capex_value.keys()))
            if not available_sizes_in_map: # Map vide
                 st.warning(f"Map CAPEX par paliers vide pour taille {size_kwc_iter} kWc. Utilisation d'un fallback CAPEX.")
                 current_capex_val = size_kwc_iter * 1000 # Fallback générique
            else:
                # Trouver la clé la plus proche (inférieure ou égale, sinon la plus petite disponible)
                suitable_keys = [k_map for k_map in available_sizes_in_map if k_map <= size_kwc_iter]
                if suitable_keys:
                    closest_size_key = max(suitable_keys)
                else: # Si toutes les clés de la map sont > size_kwc_iter, prendre la plus petite
                    closest_size_key = min(available_sizes_in_map)
                current_capex_val = float(capex_value[closest_size_key])
        else:
            st.warning(f"Type d'entrée CAPEX ('{capex_input_type}') non reconnu ou valeur CAPEX map invalide pour {size_kwc_iter} kWc. Utilisation d'un fallback.")
            current_capex_val = size_kwc_iter * 1000

        # 2. Déterminer les OPEX de base pour la taille simulée
        opex_main_per_kwc = (opex_assumptions_sim or {}).get('maintenance_per_kwc', 10.0)
        opex_insu_per_kwc = (opex_assumptions_sim or {}).get('insurance_per_kwc', 3.0)
        opex_admin_per_kwc = (opex_assumptions_sim or {}).get('admin_per_kwc', 5.0)

        prov_ond_active_sim = (opex_assumptions_sim or {}).get('provision_onduleur_active', True)
        prov_ond_cost_per_kwc_sim = (opex_assumptions_sim or {}).get('provision_onduleur_cost_per_kwc', 50.0)
        prov_ond_lifetime_sim = (opex_assumptions_sim or {}).get('provision_onduleur_lifetime', 15)

        current_iter_sites_config_dict[temp_site_id] = {
            'puissance_kwc': size_kwc_iter,
            'capex': current_capex_val,
            'site_type': 'Producteur', # Pour LCOE, on simule toujours un producteur
            'opex_maintenance': opex_main_per_kwc * size_kwc_iter,
            'opex_insurance': opex_insu_per_kwc * size_kwc_iter,
            'opex_admin': opex_admin_per_kwc * size_kwc_iter,
            'opex_onduleur_provision_site': prov_ond_active_sim,
            'opex_onduleur_total_cost_site': prov_ond_cost_per_kwc_sim * size_kwc_iter if prov_ond_active_sim else 0.0,
            'opex_onduleur_lifetime_site': prov_ond_lifetime_sim if prov_ond_active_sim else 0
        }

        # 3. Mettre à l'échelle le profil de référence (qui est déjà agrégé)
        scaled_profile_df = reference_profile_df.copy()
        if 'Temps' not in scaled_profile_df.columns:
            st.error("LCOE Sim: La colonne 'Temps' est manquante dans le profil de référence agrégé.")
            continue
        if not pd.api.types.is_datetime64_any_dtype(scaled_profile_df['Temps']):
            try:
                scaled_profile_df['Temps'] = pd.to_datetime(scaled_profile_df['Temps'])
            except Exception as e_dt_conv:
                st.warning(f"LCOE Sim: Erreur de conversion de la colonne 'Temps' du profil de référence en datetime: {e_dt_conv}. Cette taille sera ignorée.")
                continue

        scaling_factor_profile = size_kwc_iter / power_of_reference_profile
        if 'production_kwh' in scaled_profile_df.columns:
            scaled_profile_df['production_kwh'] = scaled_profile_df['production_kwh'] * scaling_factor_profile
        else:
            st.warning(f"LCOE Sim: Colonne 'production_kwh' manquante dans le profil de référence pour la taille {size_kwc_iter}kWc. LCOE non calculable.")
            results_list_lcoe.append({
                'Taille_kWc': size_kwc_iter, 
                'LCOE': np.nan, 
                'VAN_Projet_Simulee': np.nan,
                'TRI_Projet_Simule': np.nan,
                'CAPEX_Total_Utilise_Simulation': current_capex_val, 
                'OPEX_Total_Annuel_Simule': np.nan, 
                'TURPE_Annuel_Simule': np.nan,
                'Taux_Autoconsommation_Simule': np.nan, 
                'Taux_Autoproduction_Simule': np.nan
            })
            continue

        if 'consumption_kwh' in scaled_profile_df.columns:
            scaled_profile_df['consumption_kwh'] = scaled_profile_df['consumption_kwh'] * scaling_factor_profile
        else:
            scaled_profile_df['consumption_kwh'] = 0.0 # Défaut si non présent

        current_iter_sites_data_dict[temp_site_id] = scaled_profile_df

        # 4. Créer une instance d'AnalysisEngine pour cette simulation
        # Utiliser une copie de la config globale pour éviter des modifications inattendues
        current_sim_engine_config = copy.deepcopy(sim_config_global_lcoe)
        
        current_sim_engine = AnalysisEngine(
            config=current_sim_engine_config,
            scenarios=base_scenarios_dict,
            sites_data=current_iter_sites_data_dict # Dictionnaire avec UN seul site (le simulé)
        )

        # 5. Calculer les indicateurs
        # Utiliser le prix de vente moyen estimé fourni pour cette simulation
        prix_revente_a_utiliser_sim = prix_vente_moyen_estime_pour_sim \
            if prix_vente_moyen_estime_pour_sim is not None and pd.notna(prix_vente_moyen_estime_pour_sim) and prix_vente_moyen_estime_pour_sim > 0 \
            else current_sim_engine_config.get("prix_vente_initial_slider_fallback", 0.10)

        all_indicators_dict = current_sim_engine.calculate_financial_indicators(
            scenario_name=target_scenario_name_sim,
            prix_revente=prix_revente_a_utiliser_sim,
            sites_config=current_iter_sites_config_dict # Config pour le site simulé
        )

        # 6. Stocker les résultats
        # Initialiser toutes les valeurs à extraire
        lcoe_val_iter = np.nan
        opex_total_sim_annual_val = np.nan
        turpe_total_sim_annual_val = np.nan
        taux_autoconsommation_simule = np.nan
        taux_autoproduction_simule = np.nan
        npv_projet_simule = np.nan # NOUVEAU
        irr_projet_simule = np.nan # NOUVEAU

        if all_indicators_dict and not all_indicators_dict.get("error"):
            lcoe_val_iter = all_indicators_dict.get('lcoe')
            npv_projet_simule = all_indicators_dict.get('npv_project') # NOUVEAU
            irr_projet_simule = all_indicators_dict.get('irr_project') # NOUVEAU
            monthly_df_sim_res = all_indicators_dict.get('monthly_data')

            if isinstance(monthly_df_sim_res, pd.DataFrame) and not monthly_df_sim_res.empty:
                df_exploitation_sim = monthly_df_sim_res[monthly_df_sim_res['Is_Construction_Phase'] == 0.0]
                if not df_exploitation_sim.empty:
                    # S'assurer que Sim_Year_Operational existe et est numérique
                    if 'Sim_Year_Operational' in df_exploitation_sim.columns and pd.api.types.is_numeric_dtype(df_exploitation_sim['Sim_Year_Operational']):
                        first_operational_year_sim = df_exploitation_sim['Sim_Year_Operational'].min()
                        if pd.notna(first_operational_year_sim):
                            first_year_data_sim = df_exploitation_sim[df_exploitation_sim['Sim_Year_Operational'] == first_operational_year_sim]
                            if not first_year_data_sim.empty:
                                opex_total_sim_annual_val = first_year_data_sim['OPEX'].sum() if 'OPEX' in first_year_data_sim else np.nan
                                turpe_total_sim_annual_val = first_year_data_sim['TURPE'].sum() if 'TURPE' in first_year_data_sim else np.nan
                        else:
                             st.warning(f"LCOE Sim {size_kwc_iter}kWc: Année opérationnelle minimale non trouvée pour OPEX/TURPE.")
                    else:
                        st.warning(f"LCOE Sim {size_kwc_iter}kWc: Colonne 'Sim_Year_Operational' manquante ou non numérique pour OPEX/TURPE.")
                    
                    # Calcul des taux d'autoconsommation et d'autoproduction
                    total_production_sim = df_exploitation_sim['Production_kWh'].sum() if 'Production_kWh' in df_exploitation_sim.columns else 0
                    total_consommation_sim = df_exploitation_sim['Consommation_kWh'].sum() if 'Consommation_kWh' in df_exploitation_sim.columns else 0
                    total_autocons_sim = df_exploitation_sim['Autoconsommation_kWh'].sum() if 'Autoconsommation_kWh' in df_exploitation_sim.columns else 0
                    
                    if total_consommation_sim > 1e-6:  # Éviter division par zéro
                        taux_autoconsommation_simule = (total_autocons_sim / total_consommation_sim) * 100
                    if total_production_sim > 1e-6:  # Éviter division par zéro
                        taux_autoproduction_simule = (total_autocons_sim / total_production_sim) * 100


            results_list_lcoe.append({
                'Taille_kWc': size_kwc_iter,
                'LCOE': lcoe_val_iter if pd.notna(lcoe_val_iter) else np.nan,
                'VAN_Projet_Simulee': npv_projet_simule if pd.notna(npv_projet_simule) else np.nan, # NOUVEAU
                'TRI_Projet_Simule': irr_projet_simule if pd.notna(irr_projet_simule) else np.nan, # NOUVEAU
                'CAPEX_Total_Utilise_Simulation': all_indicators_dict.get('capex_scenario_final_utilise', current_capex_val),
                'OPEX_Total_Annuel_Simule': opex_total_sim_annual_val,
                'TURPE_Annuel_Simule': turpe_total_sim_annual_val,
                'Taux_Autoconsommation_Simule': taux_autoconsommation_simule,
                'Taux_Autoproduction_Simule': taux_autoproduction_simule,
            })
        else:
            error_detail = all_indicators_dict.get("error", "inconnue") if isinstance(all_indicators_dict, dict) else "calcul non concluant"
            st.warning(f"LCOE Sim pour {size_kwc_iter} kWc: Échec calcul indicateurs ({error_detail}).")
            results_list_lcoe.append({
                'Taille_kWc': size_kwc_iter, 
                'LCOE': np.nan, 
                'VAN_Projet_Simulee': np.nan, # NOUVEAU
                'TRI_Projet_Simule': np.nan, # NOUVEAU
                'CAPEX_Total_Utilise_Simulation': current_capex_val, 
                'OPEX_Total_Annuel_Simule': np.nan, 
                'TURPE_Annuel_Simule': np.nan,
                'Taux_Autoconsommation_Simule': np.nan,
                'Taux_Autoproduction_Simule': np.nan,
            })

    return pd.DataFrame(results_list_lcoe)


def create_lcoe_vs_size_chart(df_lcoe_results: pd.DataFrame, 
                             lcoe_target: float | None = None,
                             prix_vente_reference: float | None = None,
                             tarif_oa_reference: float | None = None,
                             config_seuils: dict | None = None): # NOUVEAU: Passer la config pour les seuils
    if not isinstance(df_lcoe_results, pd.DataFrame) or df_lcoe_results.empty or 'LCOE' not in df_lcoe_results.columns:
        return go.Figure(layout={"title": "Données LCOE insuffisantes ou invalides."})

    df_plot_lcoe = df_lcoe_results.dropna(subset=['LCOE']).sort_values(by='Taille_kWc')
    if df_plot_lcoe.empty:
        return go.Figure(layout={"title": "Aucune donnée LCOE valide à afficher."})

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot_lcoe['Taille_kWc'], y=df_plot_lcoe['LCOE'],
        mode='lines+markers', name='LCOE Calculé', marker=dict(size=8, color='#1f77b4'), line=dict(width=2, color='#1f77b4'),
        customdata=df_plot_lcoe[['CAPEX_Total_Utilise_Simulation', 'OPEX_Total_Annuel_Simule', 'TURPE_Annuel_Simule']],
        hovertemplate=(
            "<b>Taille: %{x:.1f} kWc</b><br>" +
            "LCOE: %{y:.4f} €/kWh<br>" +
            "CAPEX Total (simulé): %{customdata[0]:,.0f} €<br>" +
            "OPEX Annuel (simulé): %{customdata[1]:,.0f} €<br>" +
            "TURPE Annuel (simulé): %{customdata[2]:,.0f} €" +
            "<extra></extra>"
        )
    ))
    
    # Lignes horizontales de référence
    if lcoe_target is not None and pd.notna(lcoe_target) and lcoe_target > 0:
        fig.add_hline(y=lcoe_target, line_dash="dash", line_color="red",
                      annotation_text=f"LCOE Cible: {lcoe_target:.4f} €/kWh",
                      annotation_position="bottom right")
    
    if prix_vente_reference is not None and pd.notna(prix_vente_reference) and prix_vente_reference > 0:
        fig.add_hline(y=prix_vente_reference, line_dash="dash", line_color="green",
                      annotation_text=f"Prix Vente: {prix_vente_reference:.4f} €/kWh",
                      annotation_position="bottom right")
                      
    if tarif_oa_reference is not None and pd.notna(tarif_oa_reference) and tarif_oa_reference > 0:
        fig.add_hline(y=tarif_oa_reference, line_dash="dash", line_color="orange",
                      annotation_text=f"Tarif OA: {tarif_oa_reference:.4f} €/kWh",
                      annotation_position="bottom left")
    
    # --- AMÉLIORATION : Seuils réglementaires avec infobulles détaillées ---
    if config_seuils and isinstance(config_seuils, dict):
        # Définir les seuils importants et leurs caractéristiques
        seuils_a_afficher = {
            9: {"label": "Seuil 9 kWc", "type": ["Prime", "OA"]},
            36: {"label": "Seuil 36 kWc", "type": ["Prime", "OA", "TURPE"]},
            100: {"label": "Seuil 100 kWc", "type": ["Prime", "OA"]},
            250: {"label": "Seuil 250 kWc", "type": ["TURPE"]}
        }

        # S'assurer que les seuils sont dans la plage du graphique
        x_min_graph = df_plot_lcoe['Taille_kWc'].min() if not df_plot_lcoe.empty else 0
        x_max_graph = df_plot_lcoe['Taille_kWc'].max() if not df_plot_lcoe.empty else 0
        
        # Coordonnées pour les marqueurs invisibles
        seuils_x_coords = []
        seuils_y_coords = []
        seuils_hover_texts = []
        
        # Position verticale pour les marqueurs
        y_ref = 0
        if 'LCOE' in df_plot_lcoe.columns and not df_plot_lcoe.dropna(subset=['LCOE']).empty:
            y_ref = df_plot_lcoe.dropna(subset=['LCOE'])['LCOE'].mean()

        for seuil_kwc, info_seuil in seuils_a_afficher.items():
            if x_min_graph <= seuil_kwc <= x_max_graph:
                # 1. Ajouter la ligne verticale avec annotation simplifiée
                fig.add_vline(
                    x=seuil_kwc, 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="rgba(255, 0, 0, 0.5)",
                    annotation_text=info_seuil["label"], 
                    annotation_position="top left",
                    annotation_font_size=10,
                    annotation_font_color="red"
                )
                
                # 2. Préparer le texte riche pour l'infobulle
                hover_text_detail = f"<b>{info_seuil['label']}</b>"
                
                # Information sur la Prime à l'investissement
                if "Prime" in info_seuil["type"]:
                    if seuil_kwc == 9:
                        prime_avant = config_seuils.get("subvention_rate_le9", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le36", "N/A")
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                    elif seuil_kwc == 36:
                        prime_avant = config_seuils.get("subvention_rate_le36", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le100", "N/A")
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                    elif seuil_kwc == 100:
                        prime_avant = config_seuils.get("subvention_rate_le100", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le500", 
                                                       config_seuils.get("subvention_rate_gt100", "N/A"))
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                
                # Information sur le Tarif d'Obligation d'Achat
                if "OA" in info_seuil["type"]:
                    if seuil_kwc == 9:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le9", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_le36", 0)
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                    elif seuil_kwc == 36:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le36", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_le100", 0)
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                    elif seuil_kwc == 100:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le100", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_gt100", 
                                                    config_seuils.get("tarif_oa_bracket_le500", 0))
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                
                # Information sur le TURPE
                if "TURPE" in info_seuil["type"]:
                    if seuil_kwc == 36:
                        hover_text_detail += f"<br>TURPE: BT≤36kVA → BT>36kVA"
                    elif seuil_kwc == 250:
                        hover_text_detail += f"<br>TURPE: BT>36kVA → HTA"
                
                # Ajouter à nos listes pour créer la trace scatter
                seuils_x_coords.append(seuil_kwc)
                seuils_y_coords.append(y_ref)
                seuils_hover_texts.append(hover_text_detail + "<extra></extra>")
        
        # 3. Ajouter la trace scatter avec marqueurs invisibles pour les infobulles
        if seuils_x_coords:
            fig.add_trace(go.Scatter(
                x=seuils_x_coords,
                y=seuils_y_coords,
                mode='markers',
                marker=dict(color='rgba(0,0,0,0)', size=15),  # Marqueurs invisibles mais larges
                hoverinfo='text',
                hovertemplate=seuils_hover_texts,
                name='Détails des seuils (survoler)'
            ))
    
    fig.update_layout(
        title_text="LCOE en fonction de la Taille du Projet (avec seuils réglementaires)",
        xaxis_title="Taille du Projet Simulé (kWc)", yaxis_title="LCOE (€/kWh)",
        yaxis_tickformat=".4f", hovermode="closest",  # "closest" pour une meilleure précision des infobulles
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# NOUVELLE FONCTION - Graphique des taux d'autoconsommation et d'autoproduction
def create_autoconsumption_vs_size_chart(df_results: pd.DataFrame, 
                                        config_seuils: dict | None = None): # NOUVEAU: Passer la config pour les seuils
    """
    Crée un graphique montrant l'évolution des taux d'autoconsommation 
    et d'autoproduction en fonction de la taille du projet.
    """
    if not isinstance(df_results, pd.DataFrame) or df_results.empty or \
       not all(col in df_results.columns for col in ['Taille_kWc', 'Taux_Autoconsommation_Simule', 'Taux_Autoproduction_Simule']):
        return go.Figure(layout={"title": "Données d'autoconsommation insuffisantes."})

    df_plot = df_results.dropna(subset=['Taux_Autoconsommation_Simule', 'Taux_Autoproduction_Simule']).sort_values(by='Taille_kWc')
    
    if df_plot.empty:
        return go.Figure(layout={"title": "Aucune donnée d'autoconsommation valide à afficher."})

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot['Taille_kWc'], 
        y=df_plot['Taux_Autoconsommation_Simule'],
        mode='lines+markers', 
        name='Taux d\'Autoconsommation (%)<br>(Autoconso / Conso Totale)', # Légende plus explicite
        marker=dict(size=8, color='rgb(44, 160, 44)'), # Vert
        line=dict(width=2, color='rgb(44, 160, 44)'),
        hovertemplate="Taille: %{x:.1f} kWc<br>Taux Autoconso: %{y:.1f}%<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=df_plot['Taille_kWc'], 
        y=df_plot['Taux_Autoproduction_Simule'],
        mode='lines+markers', 
        name='Taux d\'Autoproduction (%)<br>(Autoconso / Prod Totale)', # Légende plus explicite
        marker=dict(size=8, color='rgb(255, 127, 14)'), # Orange
        line=dict(width=2, color='rgb(255, 127, 14)'),
        hovertemplate="Taille: %{x:.1f} kWc<br>Taux Autoprod: %{y:.1f}%<extra></extra>"
    ))

    # --- AMÉLIORATION : Seuils réglementaires avec infobulles détaillées ---
    if config_seuils and isinstance(config_seuils, dict):
        # Définir les seuils importants et leurs caractéristiques
        seuils_a_afficher = {
            9: {"label": "Seuil 9 kWc", "type": ["Prime", "OA"]},
            36: {"label": "Seuil 36 kWc", "type": ["Prime", "OA", "TURPE"]},
            100: {"label": "Seuil 100 kWc", "type": ["Prime", "OA"]},
            250: {"label": "Seuil 250 kWc", "type": ["TURPE"]}
        }

        # S'assurer que les seuils sont dans la plage du graphique
        x_min_graph = df_plot['Taille_kWc'].min() if not df_plot.empty else 0
        x_max_graph = df_plot['Taille_kWc'].max() if not df_plot.empty else 0
        
        # Coordonnées pour les marqueurs invisibles
        seuils_x_coords = []
        seuils_y_coords = []
        seuils_hover_texts = []
        
        # Position verticale pour les marqueurs (milieu de l'axe des taux)
        y_ref = 50  # Les taux sont en pourcentage, donc le milieu est vers 50%

        for seuil_kwc, info_seuil in seuils_a_afficher.items():
            if x_min_graph <= seuil_kwc <= x_max_graph:
                # 1. Ajouter la ligne verticale avec annotation simplifiée
                fig.add_vline(
                    x=seuil_kwc, 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="rgba(255, 0, 0, 0.5)",
                    annotation_text=info_seuil["label"], 
                    annotation_position="top left",
                    annotation_font_size=10,
                    annotation_font_color="red"
                )
                
                # 2. Préparer le texte riche pour l'infobulle
                hover_text_detail = f"<b>{info_seuil['label']}</b>"
                
                # Information sur la Prime à l'investissement
                if "Prime" in info_seuil["type"]:
                    if seuil_kwc == 9:
                        prime_avant = config_seuils.get("subvention_rate_le9", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le36", "N/A")
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                    elif seuil_kwc == 36:
                        prime_avant = config_seuils.get("subvention_rate_le36", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le100", "N/A")
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                    elif seuil_kwc == 100:
                        prime_avant = config_seuils.get("subvention_rate_le100", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le500", 
                                                       config_seuils.get("subvention_rate_gt100", "N/A"))
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                
                # Information sur le Tarif d'Obligation d'Achat
                if "OA" in info_seuil["type"]:
                    if seuil_kwc == 9:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le9", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_le36", 0)
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                    elif seuil_kwc == 36:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le36", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_le100", 0)
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                    elif seuil_kwc == 100:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le100", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_gt100", 
                                                    config_seuils.get("tarif_oa_bracket_le500", 0))
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                
                # Information sur le TURPE
                if "TURPE" in info_seuil["type"]:
                    if seuil_kwc == 36:
                        hover_text_detail += f"<br>TURPE: BT≤36kVA → BT>36kVA"
                    elif seuil_kwc == 250:
                        hover_text_detail += f"<br>TURPE: BT>36kVA → HTA"
                
                # Ajouter à nos listes pour créer la trace scatter
                seuils_x_coords.append(seuil_kwc)
                seuils_y_coords.append(y_ref)
                seuils_hover_texts.append(hover_text_detail + "<extra></extra>")
        
        # 3. Ajouter la trace scatter avec marqueurs invisibles pour les infobulles
        if seuils_x_coords:
            fig.add_trace(go.Scatter(
                x=seuils_x_coords,
                y=seuils_y_coords,
                mode='markers',
                marker=dict(color='rgba(0,0,0,0)', size=15),  # Marqueurs invisibles mais larges
                hoverinfo='text',
                hovertemplate=seuils_hover_texts,
                name='Détails des seuils (survoler)'
            ))

    fig.update_layout(
        title_text="Taux d'Autoconsommation & Autoproduction vs Taille (avec seuils réglementaires)",
        xaxis_title="Taille du Projet Simulé (kWc)", 
        yaxis_title="Taux (%)",
        yaxis_range=[0, 105], # Pourcentage, donc de 0 à 100 (un peu plus pour la marge)
        yaxis_ticksuffix="%",
        hovermode="closest",  # "closest" pour une meilleure précision des infobulles
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="Indicateurs :")
    )
    return fig

# NOUVELLE FONCTION - Graphique des indicateurs de rentabilité
def create_profitability_vs_size_chart(df_results: pd.DataFrame, 
                                       show_van=True, show_tri=True,
                                       config_seuils: dict | None = None): # NOUVEAU: Passer la config pour les seuils
    """
    Crée un graphique montrant la VAN Projet et/ou le TRI Projet en fonction de la taille.
    """
    if not isinstance(df_results, pd.DataFrame) or df_results.empty:
        return go.Figure(layout={"title": "Données de rentabilité insuffisantes pour le graphique."})

    # S'assurer que les colonnes nécessaires existent
    required_profit_cols = []
    if show_van: required_profit_cols.append('VAN_Projet_Simulee')
    if show_tri: required_profit_cols.append('TRI_Projet_Simule')
    if not all(col in df_results.columns for col in required_profit_cols):
        missing_cols = [col for col in required_profit_cols if col not in df_results.columns]
        st.warning(f"Colonnes de rentabilité manquantes pour le graphique : {missing_cols}")
        # On peut décider de continuer si au moins une est présente
        if not any(col in df_results.columns for col in required_profit_cols):
             return go.Figure(layout={"title": "Colonnes VAN/TRI Projet manquantes."})


    df_plot = df_results.sort_values(by='Taille_kWc').copy() # Travailler sur une copie
    
    # Créer la figure avec un axe Y secondaire si on affiche VAN et TRI
    fig = make_subplots(specs=[[{"secondary_y": show_van and show_tri}]])

    if show_van and 'VAN_Projet_Simulee' in df_plot.columns:
        df_van_plot = df_plot.dropna(subset=['VAN_Projet_Simulee'])
        if not df_van_plot.empty:
            fig.add_trace(go.Scatter(
                x=df_van_plot['Taille_kWc'], 
                y=df_van_plot['VAN_Projet_Simulee'],
                mode='lines+markers', 
                name='VAN Projet Estimée (€)',
                marker=dict(size=8, color='rgb(0, 100, 0)'), # Vert foncé
                line=dict(width=2, color='rgb(0, 100, 0)'),
                hovertemplate="Taille: %{x:.1f} kWc<br>VAN Projet: %{y:,.0f} €<extra></extra>"
            ), secondary_y=False)

    if show_tri and 'TRI_Projet_Simule' in df_plot.columns:
        # Convertir TRI en pourcentage pour l'affichage
        df_plot['TRI_Projet_Simule_Pct'] = df_plot['TRI_Projet_Simule'].apply(lambda x: x * 100 if pd.notna(x) else np.nan)
        df_tri_plot = df_plot.dropna(subset=['TRI_Projet_Simule_Pct'])
        if not df_tri_plot.empty:
            fig.add_trace(go.Scatter(
                x=df_tri_plot['Taille_kWc'], 
                y=df_tri_plot['TRI_Projet_Simule_Pct'],
                mode='lines+markers', 
                name='TRI Projet Estimé (%)',
                marker=dict(size=8, color='rgb(214, 39, 40)'), # Rouge
                line=dict(width=2, color='rgb(214, 39, 40)'),
                hovertemplate="Taille: %{x:.1f} kWc<br>TRI Projet: %{y:.2f}%<extra></extra>"
            ), secondary_y=(show_van and 'VAN_Projet_Simulee' in df_plot.columns and not df_plot.dropna(subset=['VAN_Projet_Simulee']).empty))

    # --- AMÉLIORATION : Seuils réglementaires avec infobulles détaillées ---
    if config_seuils and isinstance(config_seuils, dict):
        # Définir les seuils importants et leurs caractéristiques
        seuils_a_afficher = {
            9: {"label": "Seuil 9 kWc", "type": ["Prime", "OA"]},
            36: {"label": "Seuil 36 kWc", "type": ["Prime", "OA", "TURPE"]},
            100: {"label": "Seuil 100 kWc", "type": ["Prime", "OA"]},
            250: {"label": "Seuil 250 kWc", "type": ["TURPE"]}
        }

        # S'assurer que les seuils sont dans la plage du graphique
        x_min_graph = df_plot['Taille_kWc'].min() if not df_plot.empty else 0
        x_max_graph = df_plot['Taille_kWc'].max() if not df_plot.empty else 0
        
        # Coordonnées pour les marqueurs invisibles
        seuils_x_coords = []
        seuils_y_coords = []
        seuils_hover_texts = []
        
        # Position verticale pour les marqueurs
        y_ref = 0
        if show_van and 'VAN_Projet_Simulee' in df_plot.columns and not df_plot.dropna(subset=['VAN_Projet_Simulee']).empty:
            y_ref = df_plot.dropna(subset=['VAN_Projet_Simulee'])['VAN_Projet_Simulee'].mean()
        elif show_tri and 'TRI_Projet_Simule_Pct' in df_plot.columns and not df_plot.dropna(subset=['TRI_Projet_Simule_Pct']).empty:
            y_ref = df_plot.dropna(subset=['TRI_Projet_Simule_Pct'])['TRI_Projet_Simule_Pct'].mean()

        for seuil_kwc, info_seuil in seuils_a_afficher.items():
            if x_min_graph <= seuil_kwc <= x_max_graph:
                # 1. Ajouter la ligne verticale avec annotation simplifiée
                fig.add_vline(
                    x=seuil_kwc, 
                    line_width=1, 
                    line_dash="dash", 
                    line_color="rgba(255, 0, 0, 0.5)",
                    annotation_text=info_seuil["label"], 
                    annotation_position="top left",
                    annotation_font_size=10,
                    annotation_font_color="red"
                )
                
                # 2. Préparer le texte riche pour l'infobulle
                hover_text_detail = f"<b>{info_seuil['label']}</b>"
                
                # Information sur la Prime à l'investissement
                if "Prime" in info_seuil["type"]:
                    if seuil_kwc == 9:
                        prime_avant = config_seuils.get("subvention_rate_le9", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le36", "N/A")
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                    elif seuil_kwc == 36:
                        prime_avant = config_seuils.get("subvention_rate_le36", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le100", "N/A")
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                    elif seuil_kwc == 100:
                        prime_avant = config_seuils.get("subvention_rate_le100", "N/A")
                        prime_apres = config_seuils.get("subvention_rate_le500", 
                                                       config_seuils.get("subvention_rate_gt100", "N/A"))
                        hover_text_detail += f"<br>Prime: {prime_avant} → {prime_apres} €/kWc"
                
                # Information sur le Tarif d'Obligation d'Achat
                if "OA" in info_seuil["type"]:
                    if seuil_kwc == 9:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le9", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_le36", 0)
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                    elif seuil_kwc == 36:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le36", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_le100", 0)
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                    elif seuil_kwc == 100:
                        oa_avant = config_seuils.get("tarif_oa_bracket_le100", 0)
                        oa_apres = config_seuils.get("tarif_oa_bracket_gt100", 
                                                    config_seuils.get("tarif_oa_bracket_le500", 0))
                        hover_text_detail += f"<br>Tarif OA: {oa_avant:.4f} → {oa_apres:.4f} €/kWh"
                
                # Information sur le TURPE
                if "TURPE" in info_seuil["type"]:
                    if seuil_kwc == 36:
                        hover_text_detail += f"<br>TURPE: BT≤36kVA → BT>36kVA"
                    elif seuil_kwc == 250:
                        hover_text_detail += f"<br>TURPE: BT>36kVA → HTA"
                
                # Ajouter à nos listes pour créer la trace scatter
                seuils_x_coords.append(seuil_kwc)
                seuils_y_coords.append(y_ref)
                seuils_hover_texts.append(hover_text_detail + "<extra></extra>")
        
        # 3. Ajouter la trace scatter avec marqueurs invisibles pour les infobulles
        if seuils_x_coords:
            fig.add_trace(go.Scatter(
                x=seuils_x_coords,
                y=seuils_y_coords,
                mode='markers',
                marker=dict(color='rgba(0,0,0,0)', size=15),  # Marqueurs invisibles mais larges
                hoverinfo='text',
                hovertemplate=seuils_hover_texts,
                name='Détails des seuils (survoler)'
            ), secondary_y=False)  # Toujours sur l'axe Y primaire pour simplicité


    fig.update_layout(
        title_text="Rentabilité Projet Estimée vs Taille (avec seuils réglementaires)",
        xaxis_title="Taille du Projet Simulé (kWc)", 
        hovermode="closest",  # "closest" pour une meilleure précision des infobulles
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Configuration des axes Y
    fig.update_yaxes(title_text="VAN Projet (€)" if show_van else "TRI Projet (%)", 
                     tickformat=",.0f" if show_van else None, 
                     ticksuffix=" €" if show_van else ("%" if show_tri and not show_van else None),
                     secondary_y=False, 
                     showgrid=True if (show_van or (show_tri and not show_van)) else False # Grille sur le premier axe affiché
                    )
    if show_van and show_tri and 'TRI_Projet_Simule' in df_plot.columns and not df_plot.dropna(subset=['TRI_Projet_Simule']).empty:
        fig.update_yaxes(title_text="TRI Projet (%)", 
                         ticksuffix="%", 
                         secondary_y=True, 
                         showgrid=False) # Pas de grille pour le second axe Y pour la clarté
        
    return fig

def display_lcoe_analysis_section(analysis_engine, config, sites_config, scenarios):
    st.subheader("Analyse du LCOE par Taille de Projet")
    st.markdown("""
    Cette section simule le LCOE pour différentes tailles d'installation PV.
    Elle utilise les **profils énergétiques agrégés de votre projet actuel** comme base, qu'elle met à l'échelle.
    Les hypothèses de coûts (CAPEX, OPEX) sont initialement proposées d'après votre projet actuel mais peuvent être ajustées ci-dessous pour la simulation.
    Le TURPE est recalculé dynamiquement par le moteur pour chaque taille simulée.
    """)

    # --- Calculer les statistiques du projet actuel pour les valeurs par défaut de l'UI ---
    current_total_kwc = 0.0
    current_total_capex = 0.0
    current_total_opex_maint_annual = 0.0
    current_total_opex_insu_annual = 0.0
    current_total_opex_admin_annual = 0.0
    current_total_opex_onduleur_annual_unindexed = 0.0

    if sites_config and isinstance(sites_config, dict):
        for site_id, site_cfg_data in sites_config.items():
            if isinstance(site_cfg_data, dict) and site_cfg_data.get('site_type', 'Producteur') == 'Producteur':
                power = float(site_cfg_data.get('puissance_kwc', 0.0))
                current_total_kwc += power
                current_total_capex += float(site_cfg_data.get('capex', 0.0))
                current_total_opex_maint_annual += float(site_cfg_data.get('opex_maintenance', 0.0))
                current_total_opex_insu_annual += float(site_cfg_data.get('opex_insurance', 0.0))
                current_total_opex_admin_annual += float(site_cfg_data.get('opex_admin', 0.0))
                if site_cfg_data.get("opex_onduleur_provision_site", False):
                    cost_ond = float(site_cfg_data.get("opex_onduleur_total_cost_site", 0.0))
                    life_ond = int(site_cfg_data.get("opex_onduleur_lifetime_site", 0))
                    if life_ond > 0:
                        current_total_opex_onduleur_annual_unindexed += cost_ond / life_ond

    st.info(
        f"**Projet Actuel de Référence :** "
        f"Puissance totale configurée = **{current_total_kwc:.2f} kWc**, "
        f"CAPEX total = **{current_total_capex:,.0f} €**. "
        f"Ces valeurs sont utilisées pour les propositions de coûts ci-dessous."
    )

    default_capex_per_kwc = (current_total_capex / current_total_kwc) if current_total_kwc > 0 else 1200.0
    default_opex_maint_per_kwc = (current_total_opex_maint_annual / current_total_kwc) if current_total_kwc > 0 else 15.0
    default_opex_insu_per_kwc = (current_total_opex_insu_annual / current_total_kwc) if current_total_kwc > 0 else 3.0
    default_opex_admin_per_kwc = (current_total_opex_admin_annual / current_total_kwc) if current_total_kwc > 0 else 5.0
    # Pour la provision onduleur, on prend le coût total et la durée de vie moyens du projet actuel pour en déduire un coût/kWc annuel
    # et ensuite le coût total /kWc pour la durée de vie.
    # C'est une approximation, car la config peut être par site.
    # On utilise les valeurs globales de la config si pas mieux.
    default_opex_onduleur_lifetime = config.get("opex_onduleur_lifetime_global", 15)
    avg_annual_onduleur_cost_per_kwc = (current_total_opex_onduleur_annual_unindexed / current_total_kwc) if current_total_kwc > 0 else (config.get("opex_onduleur_total_cost_global_par_kwc", 50) / default_opex_onduleur_lifetime if default_opex_onduleur_lifetime >0 else 3.33)
    default_opex_onduleur_total_cost_per_kwc = avg_annual_onduleur_cost_per_kwc * default_opex_onduleur_lifetime

    # --- NOUVELLE INTERFACE POUR LA SÉLECTION DES TAILLES ---
    st.markdown("#### Sélection des Tailles de Projet à Simuler")
    col_min, col_max, col_step = st.columns(3)
    
    # Valeurs par défaut pour la plage de test
    default_min_kwc_val = 30.0 # Assurer float
    default_max_kwc_val = 150.0 # Assurer float

    if current_total_kwc > 0:
        # S'assurer que les calculs intermédiaires et finaux sont des flottants
        calc_min_intermediate = float(round(float(current_total_kwc) * 0.5 / 5.0)) * 5.0
        default_min_kwc_val = max(3.0, calc_min_intermediate)
        
        calc_max_intermediate = float(round(float(current_total_kwc) * 2.0 / 5.0)) * 5.0
        default_max_kwc_val = calc_max_intermediate
        
        if default_max_kwc_val <= default_min_kwc_val:
            default_max_kwc_val = float(default_min_kwc_val) + 50.0 # Assurer float
    else: # Si current_total_kwc est 0
        default_min_kwc_val = 30.0
        default_max_kwc_val = 150.0

    # Forcer le type float pour toutes les valeurs par défaut juste avant de les utiliser
    default_min_kwc_val = float(default_min_kwc_val)
    default_max_kwc_val = float(default_max_kwc_val)

    with col_min:
        min_kwc_to_test = st.number_input(
            "Taille minimale (kWc)", 
            min_value=float(3.0),        # Explicitement float
            value=default_min_kwc_val,   # Doit être float
            step=float(1.0),             # Explicitement float
            key="lcoe_min_kwc_v5_corrected", # Nouvelle clé pour forcer la réinitialisation si besoin
            format="%.1f"
        )
    with col_max:
        # min_kwc_to_test est maintenant un float retourné par st.number_input
        max_kwc_to_test = st.number_input(
            "Taille maximale (kWc)", 
            min_value=min_kwc_to_test + 1.0, # Sera float
            value=max(default_max_kwc_val, min_kwc_to_test + 5.0), # max(float,float) -> float
            step=float(1.0),                 # Explicitement float
            key="lcoe_max_kwc_v5_corrected",
            format="%.1f"
        )
    with col_step:
        step_kwc = st.number_input(
            "Pas (kWc)", 
            min_value=float(1.0),            # Explicitement float
            value=float(5.0),                # Explicitement float
            step=float(1.0),                 # Explicitement float
            key="lcoe_step_kwc_v5_corrected",
            format="%.1f"
        )

    # Générer la liste des tailles à tester
    project_sizes_to_test = []
    if max_kwc_to_test >= min_kwc_to_test and step_kwc > 0:
        try:
            # Utiliser np.arange pour plus de précision avec les flottants, puis convertir en liste d'entiers ou flottants précis
            raw_sizes = np.arange(min_kwc_to_test, max_kwc_to_test + step_kwc / 2, step_kwc) # Ajouter step/2 pour inclure la borne max si elle tombe juste
            project_sizes_to_test = [round(s, 2) for s in raw_sizes if s <= max_kwc_to_test] # Arrondir et s'assurer de ne pas dépasser max_kwc
            project_sizes_to_test = sorted(list(set(project_sizes_to_test))) # Uniques et triées
            if not project_sizes_to_test and min_kwc_to_test <= max_kwc_to_test: # Si arange n'a rien donné mais devrait
                project_sizes_to_test = [round(min_kwc_to_test,2)]
        except Exception as e_range:
            st.error(f"Erreur lors de la génération de la plage de tailles : {e_range}")
            project_sizes_to_test = []
    
    if project_sizes_to_test:
        st.caption(f"Tailles qui seront simulées : {', '.join(map(str, project_sizes_to_test))}")
    else:
        st.warning("Aucune taille à simuler avec les paramètres de plage actuels.")

    # Générer une liste de tailles par défaut pour l'affichage des paliers CAPEX (utilisée seulement pour l'interface)
    default_selection_sizes = []
    if current_total_kwc > 0:
        candidate_sizes = [round(current_total_kwc * f) for f in [0.5, 1.0, 2.0]]
        default_selection_sizes.extend(candidate_sizes)
    else:
        default_selection_sizes = [30, 100, 500]  # Valeurs par défaut si pas de projet actuel

    base_scenario_for_lcoe = st.selectbox(
        "Scénario de base (pour modificateurs inflation, dégradation, etc.)",
        options=list(scenarios.keys()), index=0, key="lcoe_base_scenario_select_v5"
    )

    # NOUVEAU CHAMP : Prix de Vente Moyen Estimé
    default_prix_vente_moyen = config.get('tarif_edf_reference', 0.20) # Fallback initial
    # Essayer de récupérer le prix optimal du scénario actuel comme meilleur défaut
    if 'constrained_optim_results' in st.session_state and \
       base_scenario_for_lcoe in st.session_state.constrained_optim_results and \
       isinstance(st.session_state.constrained_optim_results[base_scenario_for_lcoe], dict) and \
       st.session_state.constrained_optim_results[base_scenario_for_lcoe].get('prix_optimal_const') is not None:
        default_prix_vente_moyen = st.session_state.constrained_optim_results[base_scenario_for_lcoe]['prix_optimal_const']

    prix_vente_moyen_sim_input = st.number_input(
        "Prix de Vente Moyen Estimé pour l'Énergie Valorisée (€/kWh)",
        min_value=float(0.01), # Doit être positif
        value=float(round(default_prix_vente_moyen, 4)),
        step=float(0.001),
        format="%.4f",
        key="lcoe_prix_vente_moyen_ui_v6", # Clé unique
        help="Ce prix sera utilisé pour estimer la VAN et le TRI Projet pour chaque taille simulée."
    )

    lcoe_target_input = st.number_input(
        "LCOE Cible à afficher sur graphique (€/kWh, optionnel)",
        min_value=0.0, value=round(config.get('tarif_edf_reference', 0.20) * 0.75, 4),
        step=0.0001, format="%.4f", key="lcoe_target_input_ui_v5"
    )

    st.markdown("##### Hypothèses de Coûts pour l'Analyse LCOE par Taille")
    with st.expander("Afficher/Modifier les hypothèses de coûts pour la simulation LCOE", expanded=False):
        col_capex, col_opex_prov = st.columns(2)
        with col_capex:
            capex_input_type_choice = st.radio(
                "Méthode saisie CAPEX", ["Par kWc (ratio ajustable)", "Par paliers (CAPEX total)"],
                key="lcoe_capex_input_type_v5", horizontal=True
            )
            capex_value_ui = None
            if capex_input_type_choice == "Par kWc (ratio ajustable)":
                capex_value_ui = st.number_input("CAPEX (€/kWc)", value=default_capex_per_kwc, min_value=300.0, step=25.0, key="lcoe_capex_per_kwc_val_v5", format="%.0f", help=f"Proposé d'après projet actuel: {default_capex_per_kwc:.0f} €/kWc. Ajustez pour simuler des effets d'échelle.")
            else:
                default_map_str = ", ".join([f"{s}:{s*default_capex_per_kwc:.0f}" for s in sorted(list(set(default_selection_sizes[:3] + [100, 500]))) if s>0])
                capex_map_str = st.text_area("CAPEX par Paliers (taille_kWc:Total_€)",
                                             value=default_map_str,
                                             height=100, key="lcoe_capex_map_str_v5", help="Ex: 30:35000, 100:100000, 500:450000")
                try:
                    capex_value_ui = {} # Initialiser comme un dictionnaire vide
                    if capex_map_str: # Seulement si la chaîne n'est pas vide
                        try:
                            items = capex_map_str.split(',')
                            for item_str_loop in items:
                                item_str_clean = item_str_loop.strip() # Enlever les espaces autour de "taille:valeur"
                                if ':' in item_str_clean:
                                    parts = item_str_clean.split(':', 1) # Séparer seulement au premier ':'
                                    if len(parts) == 2:
                                        key_str = parts[0].strip()
                                        val_str = parts[1].strip()
                                        
                                        # Vérifier que la clé est un nombre entier et la valeur un nombre (flottant ou entier)
                                        if key_str.isdigit():
                                            try:
                                                # float() gère les entiers et les décimaux
                                                val_float = float(val_str)
                                                capex_value_ui[int(key_str)] = val_float
                                            except ValueError:
                                                # Ignorer les paires clé:valeur mal formées pour la valeur
                                                st.warning(f"Valeur CAPEX non numérique ignorée : '{val_str}' pour la clé '{key_str}' dans la map des paliers.")
                                        else:
                                            # Ignorer si la clé n'est pas un entier
                                            st.warning(f"Clé CAPEX non numérique ignorée : '{key_str}' dans la map des paliers.")
                            
                            if not capex_value_ui and capex_map_str.strip(): # Si après traitement, c'est vide mais il y avait du texte non vide
                                st.warning("Format CAPEX par paliers incorrect ou toutes les entrées étaient invalides. Aucune valeur de palier n'a été chargée.")
                        except Exception as e_map_parse: # Attraper d'autres erreurs de parsing potentielles
                            st.error(f"Erreur lors de l'interprétation de la map CAPEX par paliers : {e_map_parse}. Entrée fournie: '{capex_map_str}'")
                            capex_value_ui = {} # Réinitialiser en cas d'erreur majeure
                except Exception as e_map:
                    st.error(f"Erreur lors de la création de la map CAPEX: {e_map}")
                    capex_value_ui = {}

        with col_opex_prov:
            st.markdown("**OPEX Annuels de Base (€/kWc/an)**")
            opex_maintenance_ui = st.number_input("Maintenance", value=default_opex_maint_per_kwc, min_value=0.0, step=1.0, key="lcoe_opex_maint_v5", format="%.0f", help=f"Proposé: {default_opex_maint_per_kwc:.0f} €/kWc/an")
            opex_insurance_ui = st.number_input("Assurance", value=default_opex_insu_per_kwc, min_value=0.0, step=0.5, key="lcoe_opex_insu_v5", format="%.1f", help=f"Proposé: {default_opex_insu_per_kwc:.1f} €/kWc/an")
            opex_admin_ui = st.number_input("Gestion/Admin", value=default_opex_admin_per_kwc, min_value=0.0, step=0.5, key="lcoe_opex_admin_v5", format="%.1f", help=f"Proposé: {default_opex_admin_per_kwc:.1f} €/kWc/an")

        st.markdown("**Provision Remplacement Onduleur (pour LCOE par taille)**")
        prov_cols = st.columns([1,2,2]) # Ajuster proportions si besoin
        with prov_cols[0]:
            default_prov_ond_active_lcoe = config.get("opex_onduleur_provision_globale", True)
            prov_onduleur_active_ui = st.checkbox("Activer?", value=default_prov_ond_active_lcoe, key="lcoe_prov_ond_active_ui_v5")
        with prov_cols[1]:
            default_prov_ond_cost_lcoe = config.get("opex_onduleur_total_cost_global_par_kwc", default_opex_onduleur_total_cost_per_kwc)
            opex_onduleur_cost_per_kwc_ui = st.number_input("Coût Rempl. (€/kWc)", value=default_prov_ond_cost_lcoe, min_value=0.0, step=5.0, key="lcoe_prov_ond_cost_ui_v5", format="%.0f", disabled=not prov_onduleur_active_ui, help=f"Proposé: {default_prov_ond_cost_lcoe:.0f} €/kWc (coût total de remplacement rapporté au kWc)")
        with prov_cols[2]:
            default_prov_ond_life_lcoe = config.get("opex_onduleur_lifetime_global", 15)
            opex_onduleur_lifetime_ui = st.number_input("Durée Vie Onduleur (ans)", value=default_prov_ond_life_lcoe, min_value=1, max_value=30, step=1, key="lcoe_prov_ond_life_ui_v5", disabled=not prov_onduleur_active_ui)

    opex_assumptions_for_sim = {
        'maintenance_per_kwc': opex_maintenance_ui,
        'insurance_per_kwc': opex_insurance_ui,
        'admin_per_kwc': opex_admin_ui,
        'provision_onduleur_active': prov_onduleur_active_ui,
        'provision_onduleur_cost_per_kwc': opex_onduleur_cost_per_kwc_ui,
        'provision_onduleur_lifetime': opex_onduleur_lifetime_ui
    }

    if st.button("Lancer l'Analyse LCOE & Rentabilité par Taille", key="run_lcoe_analysis_button_ui_v6", type="primary"):
        if not project_sizes_to_test:
            st.warning("Veuillez sélectionner au moins une taille de projet.")
        elif capex_input_type_choice == "Par paliers (CAPEX total)" and (not capex_value_ui or not isinstance(capex_value_ui, dict)):
            st.warning("Veuillez définir correctement les paliers CAPEX ou utiliser le mode par kWc.")
        elif prix_vente_moyen_sim_input <= 0:
            st.warning("Veuillez entrer un prix de vente moyen estimé positif.")
        else:
            with st.spinner("Préparation du profil de référence et simulation des LCOE et indicateurs de rentabilité..."):
                base_aggregated_profile_df = None
                original_total_power_ref = 0.0 # Sera la puissance de base_aggregated_profile_df

                # `analysis_engine` est st.session_state['analysis_engine_instance']
                # `sites_config` est st.session_state.sites_config (les configs détaillées par site du projet actuel)
                if analysis_engine.sites_data and isinstance(analysis_engine.sites_data, dict) and any(not df.empty for df in analysis_engine.sites_data.values() if isinstance(df, pd.DataFrame)):
                    try:
                        # Agréger les données de tous les sites configurés pour obtenir le profil de référence.
                        # `sites_config` est crucial ici pour que aggregate_energy_data connaisse les types de sites
                        # et agrège correctement (ex: ne pas sommer la production des "Consommateur Pur").
                        temp_aggregated_data = aggregate_energy_data(analysis_engine.sites_data, sites_config)

                        if not temp_aggregated_data.empty and 'Temps' in temp_aggregated_data.columns:
                            base_aggregated_profile_df = temp_aggregated_data
                            # La puissance de référence est la puissance totale PRODUCTIVE de ces sites agrégés.
                            # `current_total_kwc` a déjà été calculé en ne sommant que les producteurs.
                            original_total_power_ref = current_total_kwc
                            if original_total_power_ref <= 0 :
                                st.warning("La puissance productive totale du projet de référence est nulle. La mise à l'échelle sera incorrecte.")
                                base_aggregated_profile_df = None # Invalider
                        else:
                            st.error("Échec de l'agrégation du profil de référence (DataFrame vide ou colonne 'Temps' manquante).")
                    except Exception as e_agg_ref:
                        st.error(f"Erreur lors de l'agrégation du profil de référence: {e_agg_ref}")
                        st.exception(traceback.format_exc())
                        base_aggregated_profile_df = None
                else:
                    st.error("Aucune donnée de site disponible pour créer un profil de référence.")

                if base_aggregated_profile_df is None or original_total_power_ref <=0 :
                     st.error("Profil de référence ou puissance de référence invalide. Analyse LCOE annulée.")
                     st.session_state['df_analysis_results_by_size'] = pd.DataFrame() # Assurer un état propre
                else:
                    st.info(f"Utilisation d'un profil de référence agrégé (basé sur vos sites) de {original_total_power_ref:.2f} kWc pour la mise à l'échelle.")
                    df_lcoe_data = simulate_lcoe_for_project_sizes(
                        reference_profile_df=base_aggregated_profile_df,
                        power_of_reference_profile=original_total_power_ref,
                        base_config_global=config,
                        base_scenarios_dict=scenarios,
                        target_scenario_name_sim=base_scenario_for_lcoe,
                        project_sizes_kwc_list=sorted(list(set(project_sizes_to_test))),
                        capex_input_type= 'per_kwc' if capex_input_type_choice == "Par kWc (ratio ajustable)" else 'total_map',
                        capex_value=capex_value_ui,
                        opex_assumptions_sim=opex_assumptions_for_sim,
                        prix_vente_moyen_estime_pour_sim=prix_vente_moyen_sim_input
                    )
                    st.session_state['df_analysis_results_by_size'] = df_lcoe_data
            st.rerun()

    if 'df_analysis_results_by_size' in st.session_state:
        df_results_lcoe_ui = st.session_state.df_analysis_results_by_size
        if not df_results_lcoe_ui.empty:
            st.markdown("---")
            st.markdown("#### Résultats de l'Analyse LCOE et Rentabilité par Taille")
            # Utiliser st.dataframe avec column_config pour un meilleur formatage
            st.dataframe(
                df_results_lcoe_ui,
                column_config={
                    "Taille_kWc": st.column_config.NumberColumn("Taille (kWc)", format="%.1f kWc"),
                    "LCOE": st.column_config.NumberColumn("LCOE (€/kWh)", format="%.4f €/kWh"),
                    "VAN_Projet_Simulee": st.column_config.NumberColumn("VAN Projet (€)", format="%d €"),
                    "TRI_Projet_Simule": st.column_config.NumberColumn("TRI Projet (%)", format="%.2f%%"),
                    "CAPEX_Total_Utilise_Simulation": st.column_config.NumberColumn("CAPEX Simulé (€)", format="%d €"),
                    "OPEX_Total_Annuel_Simule": st.column_config.NumberColumn("OPEX Annuel Simulé (€)", format="%d €"),
                    "TURPE_Annuel_Simule": st.column_config.NumberColumn("TURPE Annuel Simulé (€)", format="%d €"),
                    "Taux_Autoconsommation_Simule": st.column_config.NumberColumn("Taux Autoconsommation (%)", format="%.1f %%"),
                    "Taux_Autoproduction_Simule": st.column_config.NumberColumn("Taux Autoproduction (%)", format="%.1f %%"),
                },
                use_container_width=True,
                hide_index=True
            )

            # Récupérer les valeurs de référence pour les lignes horizontales sur le graph LCOE
            prix_vente_optimal_projet_actuel_ref = None
            if 'constrained_optim_results' in st.session_state and \
               base_scenario_for_lcoe in st.session_state.constrained_optim_results and \
               isinstance(st.session_state.constrained_optim_results[base_scenario_for_lcoe], dict) and \
               st.session_state.constrained_optim_results[base_scenario_for_lcoe].get('prix_optimal_const') is not None:
                prix_vente_optimal_projet_actuel_ref = st.session_state.constrained_optim_results[base_scenario_for_lcoe]['prix_optimal_const']
            
            tarif_oa_reference_ref = config.get('tarif_oa_bracket_le100', 0.0761) # Exemple

            # Création des onglets pour les différents graphiques
            graph_tab1, graph_tab2, graph_tab3 = st.tabs(["LCOE vs Taille", "Rentabilité (VAN/TRI) vs Taille", "Autoconsommation vs Taille"])

            with graph_tab1:
                fig_lcoe_ui = create_lcoe_vs_size_chart(
                    df_lcoe_results=df_results_lcoe_ui, 
                    lcoe_target=lcoe_target_input if lcoe_target_input > 0 else None,
                    prix_vente_reference=prix_vente_optimal_projet_actuel_ref,
                    tarif_oa_reference=tarif_oa_reference_ref,
                    config_seuils=config
                )
                if fig_lcoe_ui:
                    st.plotly_chart(fig_lcoe_ui, use_container_width=True)
            
            with graph_tab2:
                fig_profit_ui = create_profitability_vs_size_chart(
                    df_results_lcoe_ui,
                    config_seuils=config
                )
                if fig_profit_ui:
                    st.plotly_chart(fig_profit_ui, use_container_width=True)

            with graph_tab3:
                fig_autoconsumption_ui = create_autoconsumption_vs_size_chart(
                    df_results_lcoe_ui,
                    config_seuils=config
                )
                if fig_autoconsumption_ui:
                    st.plotly_chart(fig_autoconsumption_ui, use_container_width=True)
        elif 'df_analysis_results_by_size' in st.session_state: # Clé existe mais DF est vide
             st.info("L'analyse LCOE a été lancée mais n'a pas retourné de résultats. Vérifiez les paramètres ou les logs.")