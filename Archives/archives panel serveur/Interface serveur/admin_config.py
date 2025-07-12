#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'Administration Réseau - OptimPV Desktop
===============================================

Interface d'administration sécurisée pour configurer :
- Adresse IP du serveur
- Port d'écoute
- Paramètres réseau avancés

Avec authentification par login/mot de passe.
"""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger('OptimPV_Admin')

class NetworkAdminConfig:
    """Gestionnaire de configuration réseau avec authentification"""
    
    def __init__(self, config_file="network_admin_config.json"):
        # Utiliser AppData pour stocker la configuration
        appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OptimPV')
        os.makedirs(appdata_dir, exist_ok=True)
        self.config_file = os.path.join(appdata_dir, config_file)
        self.config = self._load_config()
        
    def _load_config(self):
        """Charge la configuration ou crée la configuration par défaut"""
        default_config = {
            "network": {
                "ip": "127.0.0.1",
                "port": 8501,
                "allowed_ips": ["127.0.0.1", "localhost"],
                "external_access": False,
                "custom_domain": "",
                "browser_mode": "headless_always",
                "force_headless_panel": True
            },
            "admin": {
                # Mot de passe par défaut : "admin123" (à changer !)
                "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
                "username": "admin",
                "last_login": None,
                "session_timeout": 3600  # 1 heure
            },
            "logs": {
                "enable_network_logs": True,
                "log_admin_access": True
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # Fusionner avec les valeurs par défaut pour les nouvelles clés
                for section, values in default_config.items():
                    if section not in loaded_config:
                        loaded_config[section] = values
                    else:
                        for key, value in values.items():
                            if key not in loaded_config[section]:
                                loaded_config[section][key] = value
                return loaded_config
            except Exception as e:
                logger.error(f"Erreur lecture config admin: {e}")
                return default_config
        else:
            # Première utilisation, sauvegarder la config par défaut
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config=None):
        """Sauvegarde la configuration"""
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info("Configuration admin sauvegardée")
        except Exception as e:
            logger.error(f"Erreur sauvegarde config admin: {e}")
    
    def _hash_password(self, password):
        """Hash un mot de passe avec SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """Authentifie un utilisateur"""
        stored_username = self.config["admin"]["username"]
        stored_password_hash = self.config["admin"]["password_hash"]
        
        # Vérifier si c'est toujours le mot de passe par défaut
        default_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
        is_default_password = stored_password_hash == default_hash
        
        if username == stored_username and self._hash_password(password) == stored_password_hash:
            # Mettre à jour la dernière connexion
            self.config["admin"]["last_login"] = datetime.now().isoformat()
            self._save_config()
            
            if self.config["logs"]["log_admin_access"]:
                if is_default_password:
                    logger.warning(f"Connexion admin avec mot de passe par défaut pour {username} - CHANGEMENT REQUIS")
                else:
                    logger.info(f"Connexion admin réussie pour {username}")
            
            return True
        else:
            if self.config["logs"]["log_admin_access"]:
                logger.warning(f"Tentative de connexion admin échouée pour {username}")
            return False
    
    def change_password(self, old_password, new_password):
        """Change le mot de passe administrateur"""
        if self._hash_password(old_password) == self.config["admin"]["password_hash"]:
            self.config["admin"]["password_hash"] = self._hash_password(new_password)
            self._save_config()
            logger.info("Mot de passe admin modifié")
            return True
        return False
    
    def get_network_config(self):
        """Retourne la configuration réseau actuelle"""
        return self.config["network"].copy()
    
    def update_network_config(self, new_config=None, ip=None, port=None, external_access=None, 
                            custom_domain=None, allowed_ips=None, browser_mode=None, 
                            force_headless_panel=None):
        """Met à jour la configuration réseau"""
        changes = []
        
        # Si un dictionnaire de configuration complet est fourni, l'utiliser
        if new_config is not None and isinstance(new_config, dict):
            for key, value in new_config.items():
                if key in self.config["network"] and self.config["network"][key] != value:
                    old_value = self.config["network"][key]
                    self.config["network"][key] = value
                    changes.append(f"{key}: {old_value} → {value}")
        else:
            # Sinon, utiliser les paramètres individuels (rétrocompatibilité)
            if ip is not None and ip != self.config["network"]["ip"]:
                self.config["network"]["ip"] = ip
                changes.append(f"IP: {ip}")
            
            if port is not None and port != self.config["network"]["port"]:
                self.config["network"]["port"] = int(port)
                changes.append(f"Port: {port}")
            
            if external_access is not None:
                self.config["network"]["external_access"] = external_access
                changes.append(f"Accès externe: {external_access}")
            
            if custom_domain is not None:
                self.config["network"]["custom_domain"] = custom_domain
                changes.append(f"Domaine: {custom_domain}")
            
            if allowed_ips is not None:
                self.config["network"]["allowed_ips"] = allowed_ips
                changes.append(f"IPs autorisées: {allowed_ips}")
            
            # NOUVEAU : Support des options de navigateur
            if browser_mode is not None:
                self.config["network"]["browser_mode"] = browser_mode
                changes.append(f"Mode navigateur: {browser_mode}")
            
            if force_headless_panel is not None:
                self.config["network"]["force_headless_panel"] = force_headless_panel
                changes.append(f"Headless panneau: {force_headless_panel}")
        
        if changes:
            self._save_config()
            logger.info(f"Configuration réseau mise à jour: {', '.join(changes)}")
            return True
        
        return False
    
    def reset_network_config(self):
        """Remet la configuration réseau aux valeurs par défaut"""
        try:
            default_network = {
                "ip": "127.0.0.1",
                "port": 8502,
                "external_access": False,
                "custom_domain": None,
                "allowed_ips": ["127.0.0.1", "localhost"],
                "browser_mode": "headless_always",
                "force_headless_panel": True
            }
            
            self.config["network"] = default_network
            self._save_config()
            logger.info("Configuration réseau réinitialisée aux valeurs par défaut")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation: {e}")
            return False
    
    def get_recommended_settings(self):
        """Retourne des paramètres recommandés selon l'environnement"""
        return {
            "local_only": {
                "ip": "127.0.0.1",
                "port": 8501,
                "external_access": False,
                "description": "Accès local uniquement (sécurisé)"
            },
            "network_internal": {
                "ip": "0.0.0.0",  # Écoute sur toutes les interfaces
                "port": 8080,
                "external_access": True,
                "description": "Accès réseau interne (nécessite firewall)"
            },
            "custom_domain": {
                "ip": "0.0.0.0",
                "port": 80,
                "external_access": True,
                "description": "Accès par domaine personnalisé"
            }
        }
    
    def validate_ip(self, ip):
        """Valide une adresse IP"""
        import socket
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return ip in ["localhost", "0.0.0.0"]
    
    def validate_port(self, port):
        """Valide un numéro de port"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    def test_network_config(self, ip, port):
        """Test si une configuration réseau est accessible"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            
            # Test de binding
            if ip == "0.0.0.0":
                test_ip = "127.0.0.1"
            else:
                test_ip = ip
                
            result = sock.connect_ex((test_ip, int(port)))
            sock.close()
            
            # Port libre (connection refused = OK pour notre test)
            return result != 0
        except Exception as e:
            logger.error(f"Erreur test réseau: {e}")
            return False
    
    def export_config_summary(self):
        """Exporte un résumé de configuration pour le manager réseau"""
        network_config = self.get_network_config()
        
        summary = f"""
=== CONFIGURATION RÉSEAU OPTIMPV ===
Date de génération : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Configuration actuelle :
- Adresse IP : {network_config['ip']}
- Port : {network_config['port']}
- Accès externe : {'Activé' if network_config['external_access'] else 'Désactivé'}
- Domaine personnalisé : {network_config['custom_domain'] or 'Aucun'}
- IPs autorisées : {', '.join(network_config['allowed_ips'])}

URL d'accès : http://{network_config['ip']}:{network_config['port']}

Instructions pour le manager réseau :
1. Autoriser le port {network_config['port']} en entrée
2. Configurer le DNS interne si domaine personnalisé utilisé
3. Vérifier les règles de firewall pour les IPs autorisées

Contact technique : [Votre email]
"""
        
        # Sauvegarder dans un fichier
        summary_file = f"network_config_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"Résumé de configuration exporté: {summary_file}")
        return summary_file, summary
    
    def is_using_default_password(self):
        """Vérifie si le mot de passe par défaut est encore utilisé"""
        default_hash = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"
        return self.config["admin"]["password_hash"] == default_hash


# Interface Streamlit pour l'administration
def create_admin_interface():
    """Crée l'interface d'administration Streamlit"""
    import streamlit as st
    
    st.set_page_config(
        page_title="OptimPV - Administration Réseau",
        page_icon="🔧",
        layout="wide"
    )
    
    # CSS pour l'interface admin
    st.markdown("""
    <style>
        .admin-header {
            background-color: #d32f2f;
            color: white;
            padding: 1rem;
            border-radius: 5px;
            text-align: center;
            margin-bottom: 2rem;
        }
        .warning-box {
            background-color: #fff3e0;
            border-left: 5px solid #ff9800;
            padding: 1rem;
            margin: 1rem 0;
        }
        .success-box {
            background-color: #e8f5e9;
            border-left: 5px solid #4caf50;
            padding: 1rem;
            margin: 1rem 0;
        }
        .error-box {
            background-color: #ffebee;
            border-left: 5px solid #f44336;
            padding: 1rem;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    admin_config = NetworkAdminConfig()
    
    # En-tête d'administration
    st.markdown("""
    <div class="admin-header">
        <h1>🔧 ADMINISTRATION RÉSEAU OPTIMPV</h1>
        <p>Interface sécurisée pour la configuration réseau</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Gestion de l'authentification
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_form(admin_config)
    else:
        show_admin_panel(admin_config)


def show_login_form(admin_config):
    """Affiche le formulaire de connexion"""
    import streamlit as st
    
    st.markdown("""
    <div class="warning-box">
        <h3>🔐 Authentification Requise</h3>
        <p>Cette interface est réservée aux administrateurs réseau.</p>
        <p><strong>Mot de passe par défaut :</strong> admin123 (à changer immédiatement !)</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.subheader("Connexion Administrateur")
        
        username = st.text_input("Nom d'utilisateur", value="admin")
        password = st.text_input("Mot de passe", type="password")
        
        submit_button = st.form_submit_button("Se connecter")
        
        if submit_button:
            if admin_config.authenticate(username, password):
                st.session_state.authenticated = True
                st.success("✅ Connexion réussie !")
                st.rerun()
            else:
                st.error("❌ Identifiants incorrects")


def show_admin_panel(admin_config):
    """Affiche le panneau d'administration principal"""
    import streamlit as st
    
    # Bouton de déconnexion
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Déconnexion"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Onglets d'administration
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌐 Configuration Réseau", 
        "🔒 Sécurité", 
        "📊 Monitoring", 
        "📄 Export Config"
    ])
    
    with tab1:
        show_network_config_tab(admin_config)
    
    with tab2:
        show_security_tab(admin_config)
    
    with tab3:
        show_monitoring_tab(admin_config)
    
    with tab4:
        show_export_tab(admin_config)


def show_network_config_tab(admin_config):
    """Onglet de configuration réseau"""
    import streamlit as st
    
    st.header("🌐 Configuration Réseau")
    
    current_config = admin_config.get_network_config()
    
    # Configuration actuelle
    st.subheader("📋 Configuration Actuelle")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Adresse IP", current_config['ip'])
    with col2:
        st.metric("Port", current_config['port'])
    with col3:
        st.metric("Accès Externe", "✅ Activé" if current_config['external_access'] else "❌ Désactivé")
    
    st.markdown("---")
    
    # Nouvelle configuration
    st.subheader("⚙️ Modifier la Configuration")
    
    with st.form("network_config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_ip = st.text_input(
                "Adresse IP", 
                value=current_config['ip'],
                help="127.0.0.1 = local, 0.0.0.0 = toutes interfaces"
            )
            
            new_port = st.number_input(
                "Port", 
                min_value=1, 
                max_value=65535, 
                value=current_config['port'],
                help="Port d'écoute du serveur (éviter 80, 443, 22, 21)"
            )
        
        with col2:
            external_access = st.checkbox(
                "Autoriser l'accès externe", 
                value=current_config['external_access'],
                help="Permet l'accès depuis d'autres machines du réseau"
            )
            
            custom_domain = st.text_input(
                "Domaine personnalisé (optionnel)", 
                value=current_config['custom_domain'],
                help="Ex: optimpv.monentreprise.fr"
            )
        
        # IPs autorisées
        allowed_ips_str = st.text_area(
            "IPs autorisées (une par ligne)",
            value="\n".join(current_config['allowed_ips']),
            help="Liste des adresses IP autorisées à accéder à l'application"
        )
        
        # Configurations prédéfinies
        st.subheader("🎯 Configurations Recommandées")
        recommended = admin_config.get_recommended_settings()
        
        config_choice = st.selectbox(
            "Choisir une configuration prédéfinie",
            options=["custom"] + list(recommended.keys()),
            format_func=lambda x: "Configuration personnalisée" if x == "custom" else f"{x}: {recommended[x]['description']}"
        )
        
        if config_choice != "custom":
            rec_config = recommended[config_choice]
            st.info(f"📝 Cette configuration définira : IP={rec_config['ip']}, Port={rec_config['port']}, Externe={rec_config['external_access']}")
        
        submit_button = st.form_submit_button("💾 Appliquer la Configuration")
        
        if submit_button:
            # Validation
            if not admin_config.validate_ip(new_ip):
                st.error("❌ Adresse IP invalide")
            elif not admin_config.validate_port(new_port):
                st.error("❌ Port invalide")
            else:
                # Appliquer la configuration prédéfinie si sélectionnée
                if config_choice != "custom":
                    rec_config = recommended[config_choice]
                    new_ip = rec_config['ip']
                    new_port = rec_config['port']
                    external_access = rec_config['external_access']
                
                # Parser les IPs autorisées
                allowed_ips = [ip.strip() for ip in allowed_ips_str.split('\n') if ip.strip()]
                
                # Tester la configuration
                if admin_config.test_network_config(new_ip, new_port):
                    # Appliquer les changements
                    success = admin_config.update_network_config(
                        ip=new_ip,
                        port=new_port,
                        external_access=external_access,
                        custom_domain=custom_domain,
                        allowed_ips=allowed_ips
                    )
                    
                    if success:
                        st.success("✅ Configuration mise à jour avec succès !")
                        st.warning("⚠️ Redémarrez l'application pour appliquer les changements")
                        st.rerun()
                    else:
                        st.info("ℹ️ Aucun changement détecté")
                else:
                    st.warning("⚠️ Configuration appliquée mais le test de connectivité a échoué")


def show_security_tab(admin_config):
    """Onglet de sécurité"""
    import streamlit as st
    
    st.header("🔒 Gestion de la Sécurité")
    
    # Changement de mot de passe
    st.subheader("🔑 Changer le Mot de Passe Administrateur")
    
    with st.form("password_form"):
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
    
    st.markdown("---")
    
    # Informations de sécurité
    st.subheader("🛡️ Informations de Sécurité")
    
    admin_info = admin_config.config["admin"]
    if admin_info["last_login"]:
        st.info(f"📅 Dernière connexion : {admin_info['last_login']}")
    
    st.warning("""
    ⚠️ **Recommandations de Sécurité :**
    - Changez le mot de passe par défaut immédiatement
    - Utilisez un mot de passe fort (8+ caractères, majuscules, chiffres, symboles)
    - Limitez l'accès à cette interface aux administrateurs autorisés
    - Surveillez les logs d'accès régulièrement
    """)


def show_monitoring_tab(admin_config):
    """Onglet de monitoring"""
    import streamlit as st
    import os
    
    st.header("📊 Monitoring et Logs")
    
    # Statut du fichier de configuration
    st.subheader("📁 État des Fichiers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        config_exists = os.path.exists(admin_config.config_file)
        st.metric(
            "Fichier de Configuration", 
            "✅ Présent" if config_exists else "❌ Absent",
            f"Taille: {os.path.getsize(admin_config.config_file) if config_exists else 0} bytes"
        )
    
    with col2:
        log_file = "optimpv_launcher.log"
        log_exists = os.path.exists(log_file)
        st.metric(
            "Fichier de Logs", 
            "✅ Présent" if log_exists else "❌ Absent",
            f"Taille: {os.path.getsize(log_file) if log_exists else 0} bytes"
        )
    
    # Affichage des logs récents
    st.subheader("📜 Logs Récents")
    
    if st.button("🔄 Actualiser les Logs"):
        st.rerun()
    
    if os.path.exists("optimpv_launcher.log"):
        try:
            with open("optimpv_launcher.log", 'r', encoding='utf-8') as f:
                logs = f.readlines()
            
            # Afficher les 20 dernières lignes
            recent_logs = logs[-20:] if len(logs) > 20 else logs
            
            st.text_area(
                "Logs", 
                value="".join(recent_logs),
                height=300,
                help="20 dernières entrées du fichier de log"
            )
        except Exception as e:
            st.error(f"Erreur lecture des logs : {e}")
    else:
        st.info("Aucun fichier de log trouvé")


def show_export_tab(admin_config):
    """Onglet d'export de configuration"""
    import streamlit as st
    
    st.header("📄 Export de Configuration")
    
    st.info("""
    Cette section permet d'exporter un résumé de configuration 
    à transmettre à votre manager réseau ou équipe IT.
    """)
    
    if st.button("📋 Générer le Résumé de Configuration"):
        summary_file, summary_content = admin_config.export_config_summary()
        
        st.success(f"✅ Résumé généré : {summary_file}")
        
        # Afficher le contenu
        st.subheader("📋 Contenu du Résumé")
        st.text_area("Configuration", value=summary_content, height=400)
        
        # Bouton de téléchargement
        st.download_button(
            label="💾 Télécharger le Résumé",
            data=summary_content,
            file_name=summary_file,
            mime="text/plain"
        )
    
    st.markdown("---")
    
    # Configuration JSON brute
    st.subheader("🔧 Configuration JSON (Avancé)")
    
    if st.checkbox("Afficher la configuration JSON complète"):
        st.json(admin_config.config)


if __name__ == "__main__":
    create_admin_interface() 