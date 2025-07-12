"""
Module pour l'analyse des patterns énergétiques
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from ...shared.chart_utilities import (
    apply_theme, format_number, validate_chart_data,
    COLORS, handle_chart_error
)

def create_daily_pattern_chart(results: dict | None) -> tuple[go.Figure | None, list[str] | None]:
    """
    Crée le graphique des profils journaliers moyens ET génère des suggestions.
    """
    try:
        suggestions = []
        fig = None
        
        if not validate_chart_data(results, ['hourly_aggregated_data']):
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
                    try: 
                        df['Temps'] = pd.to_datetime(df['Temps'], errors='coerce')
                    except: 
                        st.error("Conversion 'Temps' échouée pour profil journalier.")
                        return None, None
                df = df.dropna(subset=['Temps']).set_index('Temps')
            else: 
                st.error("Index non Datetime et 'Temps' manquant pour profil journalier.")
                return None, None
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols: 
            st.error(f"Colonnes manquantes pour profil journalier: {missing_cols}")
            return None, None

        # Conversion en numérique
        for col in required_cols + ['autoconsumption_kwh', 'surplus_kwh']:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                try: 
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except: 
                    df[col] = 0.0
        df = df.fillna(0.0)

        df['hour'] = df.index.hour
        
        # Calculs si colonnes manquantes
        if 'autoconsumption_kwh' not in df.columns:
            df['autoconsumption_kwh'] = np.minimum(df['production_kwh'], df['consumption_kwh'])
        if 'surplus_kwh' not in df.columns:
            df['surplus_kwh'] = (df['production_kwh'] - df['autoconsumption_kwh']).clip(lower=0)

        # Moyennes horaires
        hourly_means = df.groupby('hour')[['production_kwh', 'consumption_kwh', 'autoconsumption_kwh', 'surplus_kwh']].mean()
        if len(hourly_means) < 24:
            hourly_means = hourly_means.reindex(range(24), fill_value=0.0)

        # Analyse des patterns
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

        # Génération des suggestions
        suggestions.append("💡 **Analysez les Courbes :** Observez les moments où la production (jaune/or) dépasse la consommation (bleue) et vice-versa.")
        
        if surplus_significatif: 
            suggestions.append(f"☀️ **Fort Surplus Détecté :** Un surplus moyen important (max ~{format_number(max_surplus_jour, 1)} kWh/h) est produit en journée. **Priorité : Stockage batterie ou pilotage de charges**.")
        else: 
            suggestions.append("✔️ **Surplus Journalier Limité :** Le surplus en journée semble modéré. L'impact du stockage/pilotage pourrait être moins important.")
            
        if deficit_significatif: 
            suggestions.append(f"🌙 **Fort Déficit Détecté :** Un besoin important depuis le réseau (max ~{format_number(max_deficit_soir_matin, 1)} kWh/h) apparaît le matin/soir. Stockage ou décalage de consommations serait utile.")
        else: 
            suggestions.append("✔️ **Déficit Matin/Soir Limité :** Les pointes de consommation matin/soir semblent modérées.")
            
        if surplus_significatif or deficit_significatif: 
            suggestions.append("👥 **Mix Consommateurs :** Envisager des profils de consommation complémentaires aiderait à équilibrer les flux.")

        # Création du graphique
        fig = go.Figure()
        
        colors = {
            'production_kwh': 'gold', 
            'consumption_kwh': COLORS['primary'], 
            'autoconsumption_kwh': COLORS['success'], 
            'surplus_kwh': COLORS['warning']
        }
        
        names = {
            'production_kwh': 'Production Moyenne', 
            'consumption_kwh': 'Consommation Moyenne', 
            'autoconsumption_kwh': 'Autoconsommation Moyenne', 
            'surplus_kwh': 'Surplus Moyen'
        }
        
        for col in ['production_kwh', 'consumption_kwh', 'autoconsumption_kwh', 'surplus_kwh']:
            if col in hourly_means.columns:
                fig.add_trace(go.Scatter(
                    x=hourly_means.index, 
                    y=hourly_means[col], 
                    mode='lines+markers', 
                    name=names.get(col, col), 
                    line=dict(color=colors.get(col, 'grey')), 
                    marker=dict(size=6)
                ))
                
        fig.update_layout(
            title="Profil Journalier Moyen (Agrégé)",
            xaxis_title="Heure de la journée", 
            yaxis_title="Énergie Moyenne (kWh par heure)",
            legend_title="Flux Énergétiques",
            xaxis=dict(
                tickmode='array', 
                tickvals=list(range(0, 24)), 
                ticktext=[f"{h}h" for h in range(0, 24)]
            ),
            hovermode="x unified",
            height=500
        )
        
        return apply_theme(fig), suggestions
        
    except Exception as e:
        st.error(f"Erreur création profil journalier : {e}")
        return None, None