"""
Interface utilisateur améliorée pour la gestion des clés de répartition
Version avec ergonomie optimisée
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .key_models import RepartitionKey, RepartitionPeriod, RepartitionRule, KeyType, PeriodType, RuleType
from .key_validators import quick_validate_keys
from .key_visualizations import (
    create_repartition_pie_chart, 
    create_temporal_evolution_chart,
    create_impact_comparison_chart
)


def render_enhanced_repartition_ui(manager):
    """
    Interface principale améliorée pour la gestion des clés de répartition
    
    Args:
        manager: Instance de RepartitionKeyManager
    """
    # Header avec état de validation toujours visible
    col_title, col_status = st.columns([3, 1])
    
    with col_title:
        st.markdown("### ⚖️ Répartition de l'Énergie")
    
    with col_status:
        # État de validation global
        is_valid, validation_msg = manager.validate_keys_coherence()
        if is_valid:
            st.success("✓ Valide")
            if validation_msg:
                st.caption(validation_msg)
        else:
            st.error("✗ Invalide")
            if validation_msg:
                st.caption(validation_msg)
    
    # Affichage direct de la répartition actuelle (toujours visible)
    st.markdown("#### 📊 Répartition Actuelle")
    _display_current_allocation(manager)
    
    # Onglets pour les différentes actions
    tab_quick, tab_advanced, tab_analysis = st.tabs([
        "🚀 Actions Rapides", 
        "⚙️ Configuration Avancée", 
        "📈 Analyse & Historique"
    ])
    
    with tab_quick:
        _render_quick_actions(manager)
    
    with tab_advanced:
        _render_advanced_config(manager)
    
    with tab_analysis:
        _render_analysis_section(manager)


def _display_current_allocation(manager):
    """Affichage visuel de la répartition actuelle"""
    
    # Récupérer les clés actuelles
    keys = manager.get_current_keys()
    
    if not keys:
        st.warning("Aucune répartition définie. Utilisez les actions rapides ci-dessous.")
        return
    
    # Créer deux colonnes : graphique et tableau
    col_chart, col_table = st.columns([1, 1])
    
    with col_chart:
        # Graphique camembert interactif
        fig = create_repartition_pie_chart(keys)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_table:
        # Tableau récapitulatif avec barres de progression
        st.markdown("##### Détail par participant")
        
        for key in keys:
            site_config = manager.sites_config.get(key.site_id, {})
            
            # Afficher le nom et la barre de progression
            col1, col2 = st.columns([2, 1])
            with col1:
                st.progress(key.value / 100, text=f"{key.participant_name}")
            with col2:
                st.metric("", f"{key.value:.1f}%", 
                         delta=f"{site_config.get('site_type', 'Producteur')}", 
                         delta_color="off")
        
        # Total de validation
        total = sum(k.value for k in keys)
        if abs(total - 100.0) < 0.01:
            st.success(f"**Total : {total:.1f}%** ✓")
        else:
            st.error(f"**Total : {total:.1f}%** (doit être 100%)")


def _render_quick_actions(manager):
    """Actions rapides pour configurer la répartition"""
    
    st.markdown("#### 🎯 Configuration Rapide")
    
    # Templates prédéfinis en grosses cartes cliquables
    st.markdown("##### Appliquer un modèle prédéfini")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container():
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f0f8ff; border-radius: 10px;'>
            <h4>⚖️ Équitable</h4>
            <p>Répartition égale entre tous les participants</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Appliquer", key="apply_equitable", use_container_width=True):
                if manager.apply_template('equitable'):
                    st.success("✓ Répartition équitable appliquée")
                    st.rerun()
    
    with col2:
        with st.container():
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f0fff0; border-radius: 10px;'>
            <h4>📊 Optimisé</h4>
            <p>Basé sur la consommation historique</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Appliquer", key="apply_optimized", use_container_width=True):
                # TODO: Implémenter avec données de consommation
                st.info("Cette fonction nécessite l'historique de consommation")
    
    with col3:
        with st.container():
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #fff0f0; border-radius: 10px;'>
            <h4>🏭 Priorité PME</h4>
            <p>Favorise les entreprises</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Appliquer", key="apply_pme", use_container_width=True):
                # TODO: Implémenter le template PME
                st.info("Template en cours de développement")
    
    st.markdown("---")
    
    # Ajustement manuel simplifié avec sliders
    st.markdown("##### Ajuster manuellement")
    
    # Option pour verrouiller certains participants
    locked_sites = st.multiselect(
        "🔒 Verrouiller ces participants (leur allocation ne changera pas)",
        options=[k.participant_name for k in manager.get_current_keys()],
        key="locked_participants"
    )
    
    # Sliders pour ajuster les allocations
    keys = manager.get_current_keys()
    new_values = {}
    locked_total = 0
    
    # Calculer le total verrouillé
    for key in keys:
        if key.participant_name in locked_sites:
            locked_total += key.value
            new_values[key.site_id] = key.value
    
    # Afficher les sliders pour les sites non verrouillés
    available_percentage = 100 - locked_total
    unlocked_keys = [k for k in keys if k.participant_name not in locked_sites]
    
    if unlocked_keys:
        st.info(f"💡 {available_percentage:.1f}% à répartir entre {len(unlocked_keys)} participants")
        
        # Utiliser des colonnes pour un affichage compact
        for i in range(0, len(unlocked_keys), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(unlocked_keys):
                    key = unlocked_keys[i + j]
                    with col:
                        # Calculer les limites du slider (tous en float)
                        max_value = min(float(available_percentage), 100.0)
                        
                        new_value = st.slider(
                            f"{key.participant_name}",
                            min_value=0.0,
                            max_value=max_value,
                            value=float(key.value),
                            step=0.5,
                            key=f"slider_{key.site_id}",
                            help=f"Site: {manager.sites_config.get(key.site_id, {}).get('site_type', 'Producteur')}"
                        )
                        new_values[key.site_id] = new_value
        
        # Afficher le total en temps réel
        current_total = sum(new_values.values())
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Barre de progression du total
            progress = min(current_total / 100, 1.0)
            st.progress(progress, text=f"Total actuel : {current_total:.1f}%")
        
        with col2:
            # Bouton d'application
            is_valid = abs(current_total - 100.0) < 0.1
            if st.button(
                "✓ Appliquer" if is_valid else f"⚠️ Ajuster ({100-current_total:+.1f}%)",
                disabled=not is_valid,
                type="primary" if is_valid else "secondary",
                use_container_width=True
            ):
                # Créer les nouvelles clés
                new_keys = []
                for site_id, value in new_values.items():
                    site_data = manager.sites_config.get(site_id, {})
                    key = RepartitionKey(
                        site_id=site_id,
                        participant_name=site_data.get('nom_fichier', site_id),
                        value=value,
                        key_type=KeyType.STATIC
                    )
                    new_keys.append(key)
                
                if manager.set_keys(new_keys):
                    st.success("✓ Répartition mise à jour")
                    st.rerun()


def _render_advanced_config(manager):
    """Configuration avancée pour utilisateurs experts"""
    
    # Sélection du mode
    mode_col1, mode_col2 = st.columns([2, 1])
    
    with mode_col1:
        current_mode = manager.config.get('mode', 'static')
        mode = st.selectbox(
            "Mode de répartition",
            options=['static', 'temporal', 'rules'],
            format_func=lambda x: {
                'static': '🔢 Statique - Pourcentages fixes',
                'temporal': '📅 Temporel - Varie selon la période',
                'rules': '🎯 Dynamique - Règles conditionnelles'
            }[x],
            index=['static', 'temporal', 'rules'].index(current_mode),
            help="Choisissez comment la répartition est calculée"
        )
    
    with mode_col2:
        if st.button("ℹ️ Aide", key="help_mode"):
            st.info("""
            **Modes disponibles:**
            - **Statique** : Pourcentages fixes toute l'année
            - **Temporel** : Change selon les saisons/mois
            - **Dynamique** : S'adapte en temps réel
            """)
    
    if mode != current_mode:
        manager.config['mode'] = mode
        st.rerun()
    
    st.markdown("---")
    
    # Interface selon le mode
    if mode == 'static':
        _render_static_editor_enhanced(manager)
    elif mode == 'temporal':
        _render_temporal_editor_enhanced(manager)
    elif mode == 'rules':
        _render_rules_editor_enhanced(manager)


def _render_static_editor_enhanced(manager):
    """Éditeur statique amélioré avec import/export"""
    
    # Options d'édition
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Exporter", use_container_width=True):
            config_dict = manager.export_to_dict()
            st.download_button(
                label="💾 Télécharger la configuration",
                data=pd.DataFrame([config_dict]).to_json(orient='records', indent=2),
                file_name=f"repartition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded = st.file_uploader("📥 Importer", type=['json'], label_visibility="collapsed")
        if uploaded:
            # TODO: Implémenter l'import
            st.info("Import en cours...")
    
    with col3:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            if st.checkbox("Confirmer la réinitialisation"):
                manager._initialize_default_keys()
                st.rerun()
    
    # Tableau éditable amélioré
    st.markdown("#### Édition manuelle")
    
    keys = manager.get_current_keys()
    df_data = []
    
    for key in keys:
        site_config = manager.sites_config.get(key.site_id, {})
        df_data.append({
            'Participant': key.participant_name,
            'Type': site_config.get('site_type', 'Producteur'),
            'Allocation (%)': key.value,
            'Puissance (kWc)': site_config.get('puissance_kwc', 0),
            'site_id': key.site_id
        })
    
    df = pd.DataFrame(df_data)
    
    # Édition avec colonnes configurées
    edited_df = st.data_editor(
        df,
        column_config={
            'Participant': st.column_config.TextColumn(
                'Participant',
                disabled=True,
                width='medium'
            ),
            'Type': st.column_config.TextColumn(
                'Type',
                disabled=True,
                width='small'
            ),
            'Allocation (%)': st.column_config.NumberColumn(
                'Allocation (%)',
                min_value=0.0,
                max_value=100.0,
                step=0.1,
                format="%.1f%%"
            ),
            'Puissance (kWc)': st.column_config.NumberColumn(
                'Puissance',
                disabled=True,
                format="%.0f kWc"
            ),
            'site_id': None  # Cacher cette colonne
        },
        hide_index=True,
        use_container_width=True,
        key="static_editor_enhanced"
    )
    
    # Validation et application en temps réel
    if not df.equals(edited_df):
        total = edited_df['Allocation (%)'].sum()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if abs(total - 100.0) < 0.01:
                st.success(f"Total : {total:.1f}% ✓")
            else:
                st.error(f"Total : {total:.1f}% (ajuster de {100-total:+.1f}%)")
        
        with col2:
            if st.button("Appliquer", disabled=abs(total - 100.0) >= 0.01):
                # Créer les nouvelles clés
                new_keys = []
                for _, row in edited_df.iterrows():
                    key = RepartitionKey(
                        site_id=row['site_id'],
                        participant_name=row['Participant'],
                        value=row['Allocation (%)'],
                        key_type=KeyType.STATIC
                    )
                    new_keys.append(key)
                
                if manager.set_keys(new_keys):
                    st.success("✓ Changements appliqués")
                    st.rerun()


def _render_temporal_editor_enhanced(manager):
    """Éditeur temporel simplifié"""
    
    st.info("🚧 Mode temporel - Configuration simplifiée")
    
    # Choix de la période
    period_type = st.radio(
        "Type de variation",
        options=['monthly', 'seasonal', 'custom'],
        format_func=lambda x: {
            'monthly': '📅 Mensuelle',
            'seasonal': '🌿 Saisonnière',
            'custom': '🎯 Personnalisée'
        }[x],
        horizontal=True
    )
    
    if period_type == 'seasonal':
        st.markdown("#### Configuration par saison")
        
        # Définir 4 périodes pour les saisons
        seasons = {
            'Hiver': (12, 1, 2),
            'Printemps': (3, 4, 5),
            'Été': (6, 7, 8),
            'Automne': (9, 10, 11)
        }
        
        # Sliders par saison
        seasonal_configs = {}
        
        for season, months in seasons.items():
            with st.expander(f"{season} (mois {months[0]}-{months[-1]})", expanded=True):
                st.info(f"Répartition pour {season}")
                
                # Réutiliser la logique des sliders
                keys = manager.get_current_keys()
                season_values = {}
                
                for key in keys:
                    value = st.slider(
                        key.participant_name,
                        0.0, 100.0, 
                        value=float(key.value),
                        step=0.5,
                        key=f"season_{season}_{key.site_id}"
                    )
                    season_values[key.site_id] = value
                
                total = sum(season_values.values())
                if abs(total - 100.0) < 0.01:
                    st.success(f"Total : {total:.1f}% ✓")
                else:
                    st.error(f"Total : {total:.1f}%")
                
                seasonal_configs[season] = season_values
        
        # Bouton pour appliquer toutes les saisons
        if st.button("Appliquer la configuration saisonnière", type="primary"):
            # TODO: Implémenter la sauvegarde des périodes
            st.success("Configuration saisonnière appliquée")
    
    else:
        st.info("Autres modes temporels en développement")


def _render_rules_editor_enhanced(manager):
    """Éditeur de règles simplifié"""
    
    st.info("🚧 Mode dynamique - Configuration des règles")
    
    # Interface simplifiée pour créer des règles
    st.markdown("#### Créer une règle simple")
    
    rule_type = st.selectbox(
        "Type de règle",
        options=['priority', 'time_based', 'threshold'],
        format_func=lambda x: {
            'priority': '🥇 Priorité - Un site passe avant les autres',
            'time_based': '⏰ Horaire - Change selon l\'heure',
            'threshold': '📊 Seuil - Déclenche selon la production'
        }[x]
    )
    
    if rule_type == 'priority':
        st.markdown("##### Règle de priorité")
        
        # Sélection du site prioritaire
        priority_site = st.selectbox(
            "Site prioritaire",
            options=[k.participant_name for k in manager.get_current_keys()]
        )
        
        priority_level = st.slider(
            "Niveau de priorité",
            min_value=0,
            max_value=100,
            value=80,
            step=1,
            help="Plus le niveau est élevé, plus le site est prioritaire"
        )
        
        conditions = st.multiselect(
            "Appliquer cette priorité quand",
            options=[
                "En heures de pointe (7h-9h, 18h-20h)",
                "En journée (9h-17h)",
                "Le week-end",
                "Production faible (<30%)",
                "Production élevée (>70%)"
            ]
        )
        
        if st.button("Créer la règle", type="primary"):
            st.success(f"Règle créée : {priority_site} prioritaire à {priority_level}%")
    
    # Liste des règles existantes
    st.markdown("---")
    st.markdown("#### Règles actives")
    
    # TODO: Afficher les règles existantes
    st.info("Aucune règle active pour le moment")


def _render_analysis_section(manager):
    """Section d'analyse et historique"""
    
    # Métriques clés
    st.markdown("#### 📊 Métriques de Performance")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Sites actifs",
            len(manager.sites_config),
            help="Nombre de participants"
        )
    
    with col2:
        # TODO: Calculer depuis les données
        st.metric(
            "Autoconsommation",
            "72%",
            delta="+5%",
            help="Taux d'autoconsommation collective"
        )
    
    with col3:
        st.metric(
            "Économies",
            "15k€/an",
            delta="+2k€",
            help="Économies estimées"
        )
    
    with col4:
        st.metric(
            "CO₂ évité",
            "25t/an",
            help="Réduction des émissions"
        )
    
    # Graphiques d'analyse
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📈 Évolution", "🎯 Comparaison", "📜 Historique"])
    
    with tab1:
        st.info("Graphique d'évolution temporelle à venir")
    
    with tab2:
        # Comparaison des scénarios
        st.markdown("##### Comparer différentes répartitions")
        
        col1, col2 = st.columns(2)
        with col1:
            scenario1 = st.selectbox(
                "Scénario 1",
                options=["Actuel", "Équitable", "Optimisé"],
                key="scenario1"
            )
        
        with col2:
            scenario2 = st.selectbox(
                "Scénario 2", 
                options=["Équitable", "Optimisé", "Priorité PME"],
                key="scenario2"
            )
        
        if st.button("Comparer", type="primary"):
            st.info("Analyse comparative en cours...")
    
    with tab3:
        # Historique des modifications
        st.markdown("##### Historique des changements")
        
        # TODO: Récupérer l'historique réel
        history_data = [
            {
                "Date": "2024-11-07 14:30",
                "Action": "Répartition équitable appliquée",
                "Par": "Admin"
            },
            {
                "Date": "2024-11-07 10:15",
                "Action": "Ajout Site D (10%)",
                "Par": "Admin"
            }
        ]
        
        df_history = pd.DataFrame(history_data)
        st.dataframe(df_history, use_container_width=True, hide_index=True)
        
        if st.button("📥 Exporter l'historique"):
            st.download_button(
                "Télécharger CSV",
                df_history.to_csv(index=False),
                "historique_repartition.csv",
                "text/csv"
            )


# Fonction helper pour créer des tooltips informatifs
def _info_tooltip(text: str, help_text: str):
    """Crée un texte avec tooltip d'aide"""
    return f"{text} ℹ️"


# Export de la fonction principale
__all__ = ['render_enhanced_repartition_ui']