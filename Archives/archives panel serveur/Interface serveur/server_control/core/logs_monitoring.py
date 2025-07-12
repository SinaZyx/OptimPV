#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Monitoring des Logs
=============================

Module dédié au monitoring et à l'affichage des logs.
"""

import streamlit as st
import time
import os
from .utils import get_logs


def show_logs_monitoring_tab(server_manager):
    """Onglet de logs et monitoring"""
    
    st.header("📜 Logs et Monitoring")
    
    # Contrôles des logs
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        lines_to_show = st.selectbox("Nombre de lignes à afficher", [20, 50, 100, 200], index=1)
    
    with col2:
        if st.button("🔄 Actualiser les Logs"):
            st.rerun()
    
    with col3:
        if st.button("🗑️ Vider les Logs"):
            try:
                with open(server_manager.log_file, 'w', encoding='utf-8'):
                    pass
                st.success("Logs vidés")
                st.rerun()
            except Exception as e:
                st.error(f"Erreur: {e}")
    
    # Affichage des logs
    st.subheader(f"📋 Dernières {lines_to_show} entrées")
    
    logs = get_logs(server_manager.log_file, lines_to_show)
    
    if logs:
        log_content = ''.join(logs)
        st.text_area(
            "Logs du serveur",
            value=log_content,
            height=400,
            help="Logs en temps réel du serveur OptimPV"
        )
    else:
        st.info("Aucun log disponible")
    
    # Monitoring en temps réel
    st.markdown("---")
    st.subheader("📊 Monitoring en Temps Réel")
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Actualisation automatique (30s)")
    
    if auto_refresh:
        time.sleep(0.1)  # Éviter le rechargement immédiat
        st.rerun()
    
    # Métriques système
    col1, col2, col3 = st.columns(3)
    
    with col1:
        server_status = "🟢 EN LIGNE" if server_manager.is_server_running() else "🔴 ARRÊTÉ"
        st.metric("État du Serveur", server_status)
    
    with col2:
        log_size = os.path.getsize(server_manager.log_file) if os.path.exists(server_manager.log_file) else 0
        st.metric("Taille des Logs", f"{log_size / 1024:.1f} KB")
    
    with col3:
        uptime = "Calculé dynamiquement" if server_manager.is_server_running() else "Arrêté"
        st.metric("Temps de fonctionnement", uptime) 