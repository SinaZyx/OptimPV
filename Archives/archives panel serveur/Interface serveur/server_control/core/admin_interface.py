#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Interface d'Administration
===================================

Module simplifié pour l'interface d'administration.
"""

import streamlit as st
from .utils import check_admin_module_available


def show_admin_tab():
    """Onglet d'administration simplifié"""
    
    st.header("🔧 Administration Réseau")
    
    admin_available, NetworkAdminConfig = check_admin_module_available()
    
    if not admin_available or NetworkAdminConfig is None:
        st.error("Module d'administration non disponible")
        st.info("""
        Pour activer l'administration réseau :
        1. Assurez-vous que le fichier `admin_config.py` est présent
        2. Redémarrez l'application
        """)
        return
    
    # Gestion de l'authentification pour l'admin
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.info("""
        ### 🔐 Accès Administrateur Requis
        
        Cette section permet de configurer les paramètres réseau du serveur OptimPV.
        L'accès est réservé aux administrateurs réseau.
        """)
        
        # Formulaire de connexion admin
        admin_config = NetworkAdminConfig()
        
        with st.form("admin_login_form"):
            st.subheader("Connexion Administrateur")
            
            username = st.text_input("Nom d'utilisateur", value="admin", placeholder="Entrez l'identifiant administrateur")
            password = st.text_input("Mot de passe", type="password", placeholder="Entrez le mot de passe administrateur")
            
            submit_button = st.form_submit_button("Se connecter")
            
            if submit_button:
                if admin_config.authenticate(username, password):
                    st.session_state.admin_authenticated = True
                    st.success("✅ Connexion administrateur réussie !")
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")
        
        st.markdown("---")
        # Suppression de l'affichage du mot de passe par défaut pour la sécurité
        st.warning("⚠️ Changez le mot de passe par défaut après la première connexion !")
        st.info("💡 Contactez votre administrateur système pour les identifiants de première connexion.")
    
    else:
        # Interface d'administration simplifiée
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write("**Interface d'Administration**")
        
        with col2:
            if st.button("🚪 Déconnexion Admin"):
                st.session_state.admin_authenticated = False
                st.rerun()
        
        # Configuration réseau simplifiée
        admin_config = NetworkAdminConfig()
        
        st.subheader("🌐 Configuration Réseau")
        
        try:
            current_config = admin_config.get_network_config()
            
            # Affichage des informations actuelles
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Adresse IP", current_config['ip'])
                st.metric("Port", current_config['port'])
            
            with col2:
                st.metric("Accès externe", "✅ Activé" if current_config['external_access'] else "❌ Désactivé")
                st.metric("IPs autorisées", len(current_config.get('allowed_ips', [])))
            
            with col3:
                domain = current_config.get('custom_domain', 'Aucun')
                st.metric("Domaine", domain if domain else "Aucun")
            
            # URLs d'accès
            st.markdown("#### 🔗 URLs d'Accès")
            
            if current_config['ip'] == "127.0.0.1":
                st.info(f"🖥️ **Accès local :** http://127.0.0.1:{current_config['port']}")
            else:
                st.info(f"🖥️ **Accès local :** http://127.0.0.1:{current_config['port']}")
                st.info(f"🌐 **Accès réseau :** http://[IP_DE_VOTRE_MACHINE]:{current_config['port']}")
                
                if current_config.get('custom_domain'):
                    st.info(f"🌍 **Domaine personnalisé :** http://{current_config['custom_domain']}:{current_config['port']}")
            
            # Bouton pour accéder à la configuration complète
            st.markdown("---")
            st.info("""
            💡 **Pour une configuration avancée :**
            
            Utilisez l'interface d'administration complète disponible dans le fichier principal 
            `server_control_panel_old.py` si vous avez besoin de modifier les paramètres réseau.
            """)
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement de la configuration réseau: {str(e)}")
            
        # Gestion des mots de passe
        st.markdown("---")
        st.subheader("🔒 Gestion des Mots de Passe")
        
        # Vérification du mot de passe par défaut
        if admin_config.is_using_default_password():
            st.error("⚠️ **SÉCURITÉ CRITIQUE** : Vous utilisez encore le mot de passe par défaut !")
            st.warning("Changez immédiatement le mot de passe pour sécuriser votre installation.")
        else:
            st.success("✅ Mot de passe personnalisé configuré")
        
        with st.expander("Changer le mot de passe administrateur"):
            with st.form("password_change_form"):
                old_password = st.text_input("Mot de passe actuel", type="password")
                new_password = st.text_input("Nouveau mot de passe", type="password")
                confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")
                
                submit_password = st.form_submit_button("🔄 Changer le Mot de Passe")
                
                if submit_password:
                    if new_password != confirm_password:
                        st.error("❌ Les mots de passe ne correspondent pas")
                    elif len(new_password) < 6:
                        st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
                    elif admin_config.change_password(old_password, new_password):
                        st.success("✅ Mot de passe modifié avec succès !")
                    else:
                        st.error("❌ Mot de passe actuel incorrect")
        
        # Gestion du mot de passe OptimPV
        st.markdown("#### 🔐 Mot de Passe OptimPV Principal")
        
        with st.expander("Changer le mot de passe d'accès à OptimPV"):
            st.info("Modifiez le mot de passe requis pour accéder au panneau OptimPV principal (app.py).")
            
            # Importer les fonctions depuis app.py
            try:
                import sys
                import os
                
                # Ajouter le chemin racine du projet
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                if project_root not in sys.path:
                    sys.path.insert(0, project_root)
                
                # Importer les fonctions de gestion du mot de passe
                from app import load_panel_password, save_panel_password, hash_password
                
                with st.form("optimpv_password_change_form"):
                    current_optimpv_password = st.text_input("Mot de passe OptimPV actuel", type="password", key="current_optimpv_pwd")
                    new_optimpv_password = st.text_input("Nouveau mot de passe OptimPV", type="password", key="new_optimpv_pwd")
                    confirm_optimpv_password = st.text_input("Confirmer le nouveau mot de passe", type="password", key="confirm_optimpv_pwd")
                    
                    submit_optimpv_password = st.form_submit_button("🔄 Changer le Mot de Passe OptimPV")
                    
                    if submit_optimpv_password:
                        if not all([current_optimpv_password, new_optimpv_password, confirm_optimpv_password]):
                            st.error("❌ Veuillez remplir tous les champs.")
                        elif new_optimpv_password != confirm_optimpv_password:
                            st.error("❌ Les nouveaux mots de passe ne correspondent pas.")
                        elif len(new_optimpv_password) < 6:
                            st.error("❌ Le nouveau mot de passe doit contenir au moins 6 caractères.")
                        else:
                            # Vérifier le mot de passe actuel
                            stored_hash = load_panel_password()
                            current_hash = hash_password(current_optimpv_password)
                            
                            if current_hash == stored_hash:
                                # Sauvegarder le nouveau mot de passe
                                save_panel_password(new_optimpv_password)
                                st.success("✅ Mot de passe OptimPV modifié avec succès !")
                                st.info("Le nouveau mot de passe sera effectif lors de la prochaine connexion à OptimPV.")
                            else:
                                st.error("❌ Mot de passe OptimPV actuel incorrect.")
                
                # Afficher les informations sur le mot de passe OptimPV
                col1, col2 = st.columns(2)
                with col1:
                    st.caption("**Mot de passe par défaut :** `panel123`")
                    st.caption("**Longueur minimale :** 6 caractères")
                
                with col2:
                    # Afficher la date de dernière modification
                    try:
                        import json
                        from datetime import datetime
                        
                        password_file = os.path.join(project_root, "config", "panel_password.json")
                        if os.path.exists(password_file):
                            with open(password_file, 'r') as f:
                                password_data = json.load(f)
                            last_modified = password_data.get("last_modified", "Inconnue")
                            if last_modified != "Inconnue":
                                last_modified = datetime.fromisoformat(last_modified).strftime("%d/%m/%Y %H:%M")
                            st.caption(f"**Dernière modification :** {last_modified}")
                        else:
                            st.caption("**Dernière modification :** Jamais modifié")
                    except:
                        st.caption("**Dernière modification :** Inconnue")
                        
            except ImportError as e:
                st.error(f"❌ Impossible de charger les fonctions de gestion du mot de passe OptimPV: {str(e)}")
                st.info("Assurez-vous que le fichier app.py est accessible depuis ce module.")
        
        # Section de diagnostic système
        st.markdown("---")
        st.subheader("🔧 Diagnostic Système")
        
        with st.expander("Diagnostic et Maintenance"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Vérifier Configuration", key="check_config"):
                    from .utils import cleanup_duplicate_configs, validate_server_ports
                    
                    # Vérifier les duplications
                    success, message = cleanup_duplicate_configs()
                    if success:
                        st.success(f"✅ Configurations: {message}")
                    else:
                        st.error(f"❌ Configurations: {message}")
                    
                    # Vérifier les ports
                    success, message = validate_server_ports()
                    if success:
                        st.success(f"✅ Ports: {message}")
                    else:
                        st.warning(f"⚠️ Ports: {message}")
            
            with col2:
                if st.button("📊 Rapport Sécurité", key="security_report"):
                    st.markdown("#### 🛡️ Rapport de Sécurité")
                    
                    # Vérifications de sécurité
                    security_checks = []
                    
                    # Mot de passe par défaut
                    if admin_config.is_using_default_password():
                        security_checks.append("❌ **CRITIQUE**: Mot de passe par défaut utilisé")
                    else:
                        security_checks.append("✅ Mot de passe personnalisé")
                    
                    # Accès externe
                    if current_config.get('external_access', False):
                        security_checks.append("⚠️ **ATTENTION**: Accès externe activé")
                    else:
                        security_checks.append("✅ Accès local uniquement")
                    
                    # IPs autorisées
                    allowed_ips = current_config.get('allowed_ips', [])
                    if len(allowed_ips) > 2:
                        security_checks.append(f"⚠️ {len(allowed_ips)} IPs autorisées")
                    else:
                        security_checks.append("✅ IPs autorisées limitées")
                    
                    for check in security_checks:
                        st.write(check)
            
            # Informations système
            st.markdown("#### 📋 Informations Système")
            
            try:
                import psutil
                import platform
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Plateforme", platform.system())
                    st.metric("CPU Usage", f"{psutil.cpu_percent()}%")
                
                with col2:
                    memory = psutil.virtual_memory()
                    st.metric("RAM Usage", f"{memory.percent}%")
                    st.metric("Processus", len(psutil.pids()))
                
                with col3:
                    # Vérifier les ports en écoute
                    listening_ports = []
                    for conn in psutil.net_connections():
                        if conn.status == 'LISTEN' and hasattr(conn, 'laddr') and conn.laddr:
                            port = conn.laddr.port if hasattr(conn.laddr, 'port') else None
                            if port and port in [8501, 8502, 8503, 8504]:
                                listening_ports.append(port)
                    
                    st.metric("Ports OptimPV", len(listening_ports))
                    if listening_ports:
                        st.caption(f"Ports: {', '.join(map(str, listening_ports))}")
                        
            except ImportError:
                st.warning("Module psutil non disponible pour les métriques système") 