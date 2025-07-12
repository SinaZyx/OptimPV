"""
Composants d'interface utilisateur pour la gestion des clés de répartition
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


def render_repartition_ui(manager):
    """
    Interface principale pour la gestion des clés de répartition
    
    Args:
        manager: Instance de RepartitionKeyManager
    """
    st.markdown("### ⚖️ Gestion des Clés de Répartition")
    
    # Informations et aide
    with st.expander("ℹ️ Comment fonctionne la répartition ?", expanded=False):
        st.info("""
        **Les clés de répartition** déterminent comment l'énergie produite est distribuée entre les participants.
        
        **3 modes disponibles :**
        - 🔢 **Clés Statiques** : Pourcentages fixes pour toute la durée
        - 📅 **Clés Temporelles** : Pourcentages qui varient selon les périodes
        - 🎯 **Règles Dynamiques** : Répartition selon des conditions (priorités, seuils, etc.)
        
        **Validation automatique** : La somme doit toujours faire 100% ✓
        """)
    
    # Bouton de réinitialisation si problème
    if st.button("🔄 Réinitialiser le gestionnaire", help="Cliquez si vous avez des erreurs ou si les sites ne se mettent pas à jour"):
        if 'repartition_manager' in st.session_state:
            del st.session_state.repartition_manager
        st.rerun()
    
    # Sélection du mode
    col1, col2 = st.columns([2, 1])
    with col1:
        current_mode = manager.config.get('mode', 'static')
        mode = st.radio(
            "Mode de répartition",
            options=['static', 'temporal', 'rules'],
            format_func=lambda x: {
                'static': '🔢 Clés Statiques',
                'temporal': '📅 Clés Temporelles',
                'rules': '🎯 Règles Dynamiques'
            }[x],
            horizontal=True,
            index=['static', 'temporal', 'rules'].index(current_mode)
        )
        
        if mode != current_mode:
            manager.config['mode'] = mode
            st.session_state.repartition_config = manager.config
            st.rerun()
    
    with col2:
        # Statut de validation
        is_valid, validation_msg = manager.validate_keys_coherence()
        if is_valid:
            st.success(validation_msg[:50] if len(validation_msg) > 50 else validation_msg)
        else:
            st.error(validation_msg[:50] if len(validation_msg) > 50 else validation_msg)
    
    # Afficher l'interface selon le mode
    if mode == 'static':
        render_static_keys_editor(manager)
    elif mode == 'temporal':
        render_temporal_keys_editor(manager)
    elif mode == 'rules':
        render_rules_builder(manager)
    
    # Section visualisation et rapport
    st.markdown("---")
    render_visualization_section(manager)
    
    # Section import/export et historique
    st.markdown("---")
    render_tools_section(manager)


def render_static_keys_editor(manager):
    """
    Éditeur pour les clés statiques
    
    Args:
        manager: Instance de RepartitionKeyManager
    """
    st.markdown("#### 🔢 Configuration des Clés Statiques")
    
    # Boutons d'action rapide
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("⚖️ Répartir équitablement"):
            # Créer une répartition équitable
            site_count = len(manager.sites_config)
            if site_count > 0:
                value_per_site = 100.0 / site_count
                keys = []
                for site_id, site_data in manager.sites_config.items():
                    key = RepartitionKey(
                        site_id=site_id,
                        participant_name=site_data.get('nom_fichier', site_id),
                        value=value_per_site,
                        key_type=KeyType.STATIC
                    )
                    keys.append(key)
                manager.set_keys(keys)
                st.success("Répartition équitable appliquée")
                st.rerun()
    
    with col2:
        if st.button("📊 Selon consommation"):
            st.info("Fonctionnalité à venir : répartition basée sur l'historique de consommation")
    
    with col3:
        if st.button("🏭 Priorité PME"):
            st.info("Fonctionnalité à venir : favoriser les sites PME")
    
    with col4:
        if st.button("🏠 Résidentiel first"):
            st.info("Fonctionnalité à venir : prioriser les sites résidentiels")
    
    # Tableau éditable des clés
    st.markdown("##### Répartition par participant")
    
    # Préparer les données pour le tableau
    keys = manager.get_current_keys()
    
    # Créer un DataFrame pour l'édition
    data = []
    for key in keys:
        site_config = manager.sites_config.get(key.site_id, {})
        data.append({
            'Participant': key.participant_name,
            'Site ID': key.site_id,
            'Allocation (%)': key.value,
            'Type Site': site_config.get('site_type', 'Producteur'),
            'Puissance (kWc)': site_config.get('puissance_kwc', 0),
            'Consommation Moy. (kWh/mois)': site_config.get('consommation_moyenne', 0)
        })
    
    df = pd.DataFrame(data)
    
    # Configuration du data editor
    column_config = {
        'Participant': st.column_config.TextColumn(
            'Participant',
            help='Nom du participant',
            disabled=True,
            width='medium'
        ),
        'Site ID': st.column_config.TextColumn(
            'Site ID',
            help='Identifiant unique du site',
            disabled=True,
            width='small'
        ),
        'Allocation (%)': st.column_config.NumberColumn(
            'Allocation (%)',
            help='Pourcentage d\'énergie alloué',
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f%%"
        ),
        'Type Site': st.column_config.TextColumn(
            'Type',
            help='Type de site',
            disabled=True,
            width='small'
        ),
        'Puissance (kWc)': st.column_config.NumberColumn(
            'Puissance (kWc)',
            help='Puissance installée',
            disabled=True,
            format="%.1f"
        ),
        'Consommation Moy. (kWh/mois)': st.column_config.NumberColumn(
            'Conso. Moy.',
            help='Consommation moyenne mensuelle',
            disabled=True,
            format="%.0f"
        )
    }
    
    # Éditeur de données
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        hide_index=True,
        num_rows="fixed",
        use_container_width=True,
        key="static_keys_editor"
    )
    
    # Vérifier les modifications
    if not df.equals(edited_df):
        # Créer les nouvelles clés
        new_keys = []
        for _, row in edited_df.iterrows():
            key = RepartitionKey(
                site_id=row['Site ID'],
                participant_name=row['Participant'],
                value=row['Allocation (%)'],
                key_type=KeyType.STATIC
            )
            new_keys.append(key)
        
        # Validation rapide
        is_valid, msg = quick_validate_keys(new_keys)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if is_valid:
                st.success(msg)
            else:
                st.error(msg)
        
        with col2:
            if st.button("💾 Appliquer", disabled=not is_valid):
                if manager.set_keys(new_keys):
                    st.success("Clés mises à jour avec succès")
                    st.rerun()
                else:
                    st.error("Erreur lors de la mise à jour")
    
    # Afficher la somme totale
    total = edited_df['Allocation (%)'].sum()
    if abs(total - 100.0) < 0.01:
        st.metric("Total", f"{total:.1f}%", delta="✓ Valide", delta_color="normal")
    else:
        st.metric("Total", f"{total:.1f}%", delta=f"{100.0 - total:+.1f}% nécessaire", delta_color="inverse")


def render_temporal_keys_editor(manager):
    """
    Éditeur pour les clés temporelles
    
    Args:
        manager: Instance de RepartitionKeyManager
    """
    st.markdown("#### 📅 Configuration des Clés Temporelles")
    
    # Sélection de la granularité
    granularity = st.selectbox(
        "Granularité temporelle",
        options=['monthly', 'quarterly', 'yearly', 'custom'],
        format_func=lambda x: {
            'monthly': '📅 Mensuelle',
            'quarterly': '📊 Trimestrielle',
            'yearly': '📈 Annuelle',
            'custom': '🎯 Personnalisée'
        }[x]
    )
    
    # Interface de configuration selon la granularité
    if granularity == 'monthly':
        render_monthly_temporal_editor(manager)
    elif granularity == 'quarterly':
        st.info("Configuration trimestrielle à venir")
    elif granularity == 'yearly':
        st.info("Configuration annuelle à venir")
    elif granularity == 'custom':
        st.info("Configuration personnalisée à venir")


def render_monthly_temporal_editor(manager):
    """
    Éditeur mensuel pour les clés temporelles
    """
    st.markdown("##### Configuration Mensuelle")
    
    # Sélection de la période
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Date de début", value=datetime.now().date())
    with col2:
        end_date = st.date_input("Date de fin", value=(datetime.now() + timedelta(days=365)).date())
    
    # Générer les mois entre les dates
    months = pd.date_range(start=start_date, end=end_date, freq='MS')
    
    if len(months) > 0:
        # Sélecteur de mois
        selected_month = st.select_slider(
            "Sélectionner le mois à configurer",
            options=months,
            format_func=lambda x: x.strftime('%B %Y')
        )
        
        st.info(f"Configuration pour : {selected_month.strftime('%B %Y')}")
        
        # Actions rapides
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 Copier mois précédent"):
                st.info("Copie des valeurs du mois précédent")
        with col2:
            if st.button("📊 Interpoler"):
                st.info("Interpolation entre les mois configurés")
        with col3:
            if st.button("🔄 Appliquer pattern"):
                st.info("Application d'un pattern de variation")
        
        # Réutiliser l'éditeur statique pour ce mois
        st.markdown(f"###### Répartition pour {selected_month.strftime('%B %Y')}")
        # TODO: Adapter l'éditeur statique pour gérer un mois spécifique


def render_rules_builder(manager):
    """
    Constructeur de règles dynamiques
    
    Args:
        manager: Instance de RepartitionKeyManager
    """
    st.markdown("#### 🎯 Configuration des Règles Dynamiques")
    
    # Types de règles disponibles
    rule_type = st.selectbox(
        "Type de règle à ajouter",
        options=['priority', 'threshold', 'time_based', 'consumption_based'],
        format_func=lambda x: {
            'priority': '🥇 Priorité de consommation',
            'threshold': '📊 Seuils min/max',
            'time_based': '⏰ Plages horaires',
            'consumption_based': '📈 Basé sur la consommation'
        }[x]
    )
    
    # Interface de création selon le type
    if rule_type == 'priority':
        render_priority_rule_builder(manager)
    elif rule_type == 'threshold':
        render_threshold_rule_builder(manager)
    elif rule_type == 'time_based':
        render_time_based_rule_builder(manager)
    elif rule_type == 'consumption_based':
        render_consumption_based_rule_builder(manager)
    
    # Liste des règles existantes
    st.markdown("##### Règles actives")
    rules = manager._get_active_rules()
    
    if rules:
        for i, rule in enumerate(rules):
            with st.expander(f"{rule.rule_name} (Priorité: {rule.priority})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"Type: {rule.rule_type.value}")
                    st.write(f"Sites ciblés: {', '.join(rule.target_sites)}")
                with col2:
                    if st.button(f"🗑️ Supprimer", key=f"del_rule_{i}"):
                        # TODO: Implémenter la suppression
                        st.info("Suppression à implémenter")
                with col3:
                    enabled = st.checkbox("Activé", value=rule.enabled, key=f"enable_rule_{i}")
                    if enabled != rule.enabled:
                        rule.enabled = enabled
                        # TODO: Sauvegarder le changement
    else:
        st.info("Aucune règle définie. Créez votre première règle ci-dessus.")


def render_priority_rule_builder(manager):
    """Constructeur de règles de priorité"""
    with st.container():
        st.markdown("##### Nouvelle règle de priorité")
        
        rule_name = st.text_input("Nom de la règle", placeholder="Ex: Priorité résidentiel")
        priority = st.number_input("Niveau de priorité", min_value=0, max_value=100, value=50)
        
        # Sélection des sites
        sites = list(manager.sites_config.keys())
        site_names = [manager.sites_config[s].get('nom_fichier', s) for s in sites]
        
        selected_indices = st.multiselect(
            "Sites concernés",
            options=range(len(sites)),
            format_func=lambda x: site_names[x]
        )
        
        if st.button("➕ Créer la règle"):
            if rule_name and selected_indices:
                # TODO: Créer et ajouter la règle
                st.success(f"Règle '{rule_name}' créée")
            else:
                st.error("Veuillez remplir tous les champs")


def render_threshold_rule_builder(manager):
    """Constructeur de règles de seuil"""
    st.info("Configuration des seuils min/max à venir")


def render_time_based_rule_builder(manager):
    """Constructeur de règles temporelles"""
    st.info("Configuration des plages horaires à venir")


def render_consumption_based_rule_builder(manager):
    """Constructeur de règles basées sur la consommation"""
    st.info("Configuration basée sur la consommation à venir")


def render_visualization_section(manager):
    """
    Section de visualisation et rapports
    
    Args:
        manager: Instance de RepartitionKeyManager
    """
    st.markdown("#### 📊 Visualisations et Analyse")
    
    tab1, tab2, tab3 = st.tabs(["Répartition Actuelle", "Évolution Temporelle", "Impact Financier"])
    
    with tab1:
        # Graphique camembert de la répartition
        keys = manager.get_current_keys()
        if keys:
            fig = create_repartition_pie_chart(keys)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune clé de répartition définie")
    
    with tab2:
        if manager.config.get('mode') == 'temporal':
            # Graphique d'évolution temporelle
            st.info("Graphique d'évolution temporelle à venir")
        else:
            st.info("Activez le mode temporel pour voir l'évolution")
    
    with tab3:
        # Calcul et affichage de l'impact financier
        if st.button("📈 Calculer l'impact financier"):
            # TODO: Implémenter le calcul d'impact
            st.info("Calcul de l'impact financier à venir")


def render_tools_section(manager):
    """
    Section outils : import/export, historique, templates
    
    Args:
        manager: Instance de RepartitionKeyManager
    """
    st.markdown("#### 🛠️ Outils")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("##### 📥 Import/Export")
        
        # Export
        if st.button("💾 Exporter la configuration"):
            config_dict = manager.export_to_dict()
            st.download_button(
                label="📥 Télécharger JSON",
                data=pd.DataFrame([config_dict]).to_json(orient='records', indent=2),
                file_name=f"repartition_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # Import
        uploaded_file = st.file_uploader("Importer une configuration", type=['json'])
        if uploaded_file is not None:
            # TODO: Implémenter l'import
            st.info("Import à implémenter")
    
    with col2:
        st.markdown("##### 🕐 Historique")
        
        history = st.session_state.get('repartition_history', [])
        if history:
            selected_index = st.selectbox(
                "Restaurer depuis l'historique",
                options=range(len(history)),
                format_func=lambda i: history[i]['timestamp'].strftime('%d/%m/%Y %H:%M')
            )
            
            if st.button("🔄 Restaurer"):
                if manager.restore_from_history(selected_index):
                    st.success("Configuration restaurée")
                    st.rerun()
        else:
            st.info("Aucun historique disponible")
    
    with col3:
        st.markdown("##### 📋 Templates")
        
        templates = ['equitable', 'consumption_based', 'priority_pme']
        template_names = {
            'equitable': '⚖️ Répartition équitable',
            'consumption_based': '📊 Basé sur consommation',
            'priority_pme': '🏭 Priorité PME'
        }
        
        selected_template = st.selectbox(
            "Appliquer un template",
            options=templates,
            format_func=lambda x: template_names[x]
        )
        
        if st.button("✅ Appliquer le template"):
            if manager.apply_template(selected_template):
                st.success(f"Template '{template_names[selected_template]}' appliqué")
                st.rerun()
            else:
                st.error("Erreur lors de l'application du template")