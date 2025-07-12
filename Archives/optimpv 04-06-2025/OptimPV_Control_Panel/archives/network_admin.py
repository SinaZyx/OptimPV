# panel/network_admin.py
"""
Module d'administration réseau sécurisé
"""

import streamlit as st
import ipaddress
import socket
import netifaces
from typing import List, Dict
import re
from datetime import datetime

from utils.logger import SecureLogger
from config.settings import config_manager


class NetworkAdminModule:
    """Interface d'administration réseau (zone sécurisée)"""
    
    def __init__(self, security_core):
        self.security_core = security_core
        self.logger = SecureLogger()
        
    def render(self):
        """Afficher l'interface d'admin réseau"""
        st.markdown("### 🌐 Configuration Réseau - Zone Sécurisée")
        
        # Avertissement sécurité
        st.warning("⚠️ **Zone d'administration** - Toutes les modifications sont journalisées")
        
        # Tabs de configuration
        tab1, tab2, tab3, tab4 = st.tabs([
            "Configuration IP", 
            "Liste Blanche IP", 
            "Pare-feu", 
            "Diagnostics"
        ])
        
        with tab1:
            self._render_ip_config()
        
        with tab2:
            self._render_ip_whitelist()
        
        with tab3:
            self._render_firewall_config()
        
        with tab4:
            self._render_network_diagnostics()
    
    def _render_ip_config(self):
        """Configuration des paramètres IP"""
        st.markdown("#### ⚙️ Paramètres Réseau du Serveur")
        
        # Charger config actuelle
        network_config = config_manager.get_section('network') or {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Interfaces disponibles
            interfaces = self._get_network_interfaces()
            selected_interface = st.selectbox(
                "Interface réseau",
                options=list(interfaces.keys()),
                index=0 if interfaces else None,
                help="Sélectionner l'interface réseau à utiliser"
            )
            
            if selected_interface and interfaces:
                st.info(f"IP actuelle: {interfaces[selected_interface]}")
            
            # Adresse de liaison
            bind_address = st.text_input(
                "Adresse IP de liaison",
                value=network_config.get('bind_address', '127.0.0.1'),
                help="0.0.0.0 pour écouter sur toutes les interfaces"
            )
            
            # Validation IP
            if not self._validate_ip(bind_address):
                st.error("❌ Adresse IP invalide")
        
        with col2:
            # Port
            port = st.number_input(
                "Port d'écoute",
                min_value=1024,
                max_value=65535,
                value=network_config.get('port', 8501),
                help="Ports 1024-65535 recommandés"
            )
            
            # Vérifier disponibilité port
            if not self._check_port_available(bind_address, port):
                st.error(f"❌ Port {port} déjà utilisé")
            
            # Options avancées
            st.markdown("**Options avancées**")
            
            enable_ssl = st.checkbox(
                "Activer SSL/TLS",
                value=network_config.get('enable_ssl', False),
                help="Nécessite un certificat valide"
            )
            
            if enable_ssl:
                ssl_cert = st.text_input(
                    "Chemin certificat SSL",
                    value=network_config.get('ssl_cert', '')
                )
                ssl_key = st.text_input(
                    "Chemin clé privée",
                    value=network_config.get('ssl_key', ''),
                    type="password"
                )
        
        # DNS personnalisé
        st.markdown("#### 🌐 Configuration DNS")
        
        enable_custom_domain = st.checkbox(
            "Activer domaine personnalisé",
            value=network_config.get('enable_custom_domain', False)
        )
        
        if enable_custom_domain:
            custom_domain = st.text_input(
                "Nom de domaine",
                value=network_config.get('custom_domain', 'optimv.local'),
                help="Exemple: optimv.local, solar.company.com"
            )
            
            # Validation domaine
            if not self._validate_domain(custom_domain):
                st.error("❌ Nom de domaine invalide")
        
        # Sauvegarder
        if st.button("💾 Sauvegarder Configuration IP", type="primary"):
            new_config = {
                'bind_address': bind_address,
                'port': port,
                'interface': selected_interface,
                'enable_ssl': enable_ssl,
                'enable_custom_domain': enable_custom_domain
            }
            
            if enable_ssl:
                new_config['ssl_cert'] = ssl_cert
                new_config['ssl_key'] = ssl_key
            
            if enable_custom_domain:
                new_config['custom_domain'] = custom_domain
            
            # Valider avant sauvegarde
            if self._validate_network_config(new_config):
                config_manager.update_section('network', new_config)
                st.success("✅ Configuration réseau sauvegardée")
                
                # Logger
                self.logger.log_security_event('NETWORK_CONFIG_CHANGE', {
                    'admin': 'current_user',
                    'changes': new_config
                })
            else:
                st.error("❌ Configuration invalide")
    
    def _render_ip_whitelist(self):
        """Gestion de la liste blanche IP"""
        st.markdown("#### 🔐 Liste Blanche des Adresses IP")
        
        st.info("Seules les adresses IP listées pourront accéder au serveur")
        
        # Charger liste actuelle
        whitelist = config_manager.get('network.ip_whitelist', [])
        
        # Afficher liste actuelle
        if whitelist:
            st.markdown("**Adresses autorisées:**")
            
            # Tableau avec actions
            for idx, entry in enumerate(whitelist):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    if isinstance(entry, dict):
                        st.text(entry.get('ip', 'N/A'))
                    else:
                        st.text(entry)
                
                with col2:
                    if isinstance(entry, dict):
                        st.caption(entry.get('description', ''))
                
                with col3:
                    if isinstance(entry, dict):
                        st.caption(entry.get('added_date', ''))
                
                with col4:
                    if st.button("🗑️", key=f"del_ip_{idx}"):
                        whitelist.pop(idx)
                        config_manager.set('network.ip_whitelist', whitelist)
                        st.rerun()
        else:
            st.warning("Aucune restriction IP configurée")
        
        # Ajouter nouvelle IP
        st.markdown("---")
        st.markdown("**Ajouter une adresse IP:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_ip = st.text_input(
                "Adresse IP ou plage CIDR",
                placeholder="192.168.1.100 ou 192.168.1.0/24"
            )
            
            # Validation
            ip_valid = False
            if new_ip:
                if '/' in new_ip:
                    # CIDR
                    try:
                        ipaddress.ip_network(new_ip, strict=False)
                        ip_valid = True
                    except:
                        st.error("❌ Plage CIDR invalide")
                else:
                    # IP simple
                    if self._validate_ip(new_ip):
                        ip_valid = True
                    else:
                        st.error("❌ Adresse IP invalide")
        
        with col2:
            description = st.text_input(
                "Description",
                placeholder="Poste administrateur"
            )
        
        if st.button("➕ Ajouter à la liste blanche", disabled=not ip_valid):
            entry = {
                'ip': new_ip,
                'description': description,
                'added_date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'added_by': 'admin'
            }
            
            whitelist.append(entry)
            config_manager.set('network.ip_whitelist', whitelist)
            
            st.success(f"✅ {new_ip} ajouté à la liste blanche")
            
            # Logger
            self.logger.log_security_event('IP_WHITELIST_ADD', {
                'ip': new_ip,
                'description': description
            })
            
            st.rerun()
        
        # Actions globales
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Importer liste", use_container_width=True):
                st.info("TODO: Import depuis fichier")
        
        with col2:
            if st.button("📤 Exporter liste", use_container_width=True):
                # TODO: Export
                st.download_button(
                    "Télécharger",
                    data=str(whitelist),
                    file_name="ip_whitelist.json",
                    mime="application/json"
                )
    
    def _render_firewall_config(self):
        """Configuration du pare-feu"""
        st.markdown("#### 🛡️ Configuration Pare-feu")
        
        # État du pare-feu
        firewall_enabled = config_manager.get('network.firewall_enabled', True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if firewall_enabled:
                st.success("🟢 ACTIF")
            else:
                st.error("🔴 INACTIF")
        
        with col2:
            new_state = st.checkbox(
                "Activer le pare-feu intégré",
                value=firewall_enabled
            )
            
            if new_state != firewall_enabled:
                config_manager.set('network.firewall_enabled', new_state)
                st.rerun()
        
        if firewall_enabled:
            # Règles de pare-feu
            st.markdown("**Règles actives:**")
            
            rules = config_manager.get('network.firewall_rules', self._get_default_rules())
            
            # Afficher règles
            for idx, rule in enumerate(rules):
                with st.expander(f"Règle {idx + 1}: {rule['name']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.text(f"Action: {rule['action']}")
                        st.text(f"Protocole: {rule['protocol']}")
                    
                    with col2:
                        st.text(f"Source: {rule['source']}")
                        st.text(f"Destination: {rule['destination']}")
                    
                    with col3:
                        st.text(f"Port: {rule['port']}")
                        if st.button("🗑️ Supprimer", key=f"del_rule_{idx}"):
                            rules.pop(idx)
                            config_manager.set('network.firewall_rules', rules)
                            st.rerun()
            
            # Ajouter règle
            if st.checkbox("➕ Ajouter une règle"):
                self._render_add_firewall_rule(rules)
        
        # Paramètres avancés
        with st.expander("⚙️ Paramètres avancés"):
            block_countries = st.multiselect(
                "Bloquer pays (codes ISO)",
                options=['CN', 'RU', 'KP', 'IR'],
                default=config_manager.get('network.blocked_countries', [])
            )
            
            rate_limit = st.number_input(
                "Limite de requêtes/minute",
                min_value=10,
                max_value=1000,
                value=config_manager.get('network.rate_limit', 100)
            )
            
            if st.button("Sauvegarder paramètres avancés"):
                config_manager.set('network.blocked_countries', block_countries)
                config_manager.set('network.rate_limit', rate_limit)
                st.success("✅ Paramètres sauvegardés")
    
    def _render_network_diagnostics(self):
        """Outils de diagnostic réseau"""
        st.markdown("#### 🔍 Diagnostics Réseau")
        
        # Tests de connectivité
        st.markdown("**Tests de connectivité:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            test_host = st.text_input(
                "Hôte à tester",
                value="google.com"
            )
            
            if st.button("🔍 Ping", use_container_width=True):
                with st.spinner("Test en cours..."):
                    result = self._ping_host(test_host)
                    if result['success']:
                        st.success(f"✅ Réponse en {result['time']}ms")
                    else:
                        st.error(f"❌ {result['error']}")
        
        with col2:
            test_port = st.number_input(
                "Port à tester",
                min_value=1,
                max_value=65535,
                value=80
            )
            
            if st.button("🔌 Test port", use_container_width=True):
                with st.spinner("Test en cours..."):
                    if self._test_port(test_host, test_port):
                        st.success(f"✅ Port {test_port} ouvert")
                    else:
                        st.error(f"❌ Port {test_port} fermé")
        
        # Informations réseau
        st.markdown("---")
        st.markdown("**Informations système:**")
        
        # Interfaces réseau
        with st.expander("📡 Interfaces réseau"):
            interfaces = self._get_detailed_network_info()
            for name, info in interfaces.items():
                st.markdown(f"**{name}:**")
                for key, value in info.items():
                    st.text(f"  {key}: {value}")
        
        # Table de routage
        with st.expander("🗺️ Table de routage"):
            routes = self._get_routing_table()
            if routes:
                st.dataframe(routes, use_container_width=True)
            else:
                st.info("Impossible de récupérer la table de routage")
        
        # Connexions actives
        with st.expander("🔗 Connexions actives"):
            connections = self._get_active_connections()
            if connections:
                st.dataframe(connections, use_container_width=True)
            else:
                st.info("Aucune connexion active")
        
        # Export diagnostics
        if st.button("📥 Exporter rapport diagnostic complet"):
            report = self._generate_diagnostic_report()
            st.download_button(
                "Télécharger rapport",
                data=report,
                file_name=f"network_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    def _get_network_interfaces(self) -> Dict[str, str]:
        """Obtenir les interfaces réseau disponibles"""
        interfaces = {}
        
        try:
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if ip != '127.0.0.1':
                            interfaces[iface] = ip
        except:
            # Fallback
            interfaces['localhost'] = '127.0.0.1'
        
        return interfaces
    
    def _validate_ip(self, ip: str) -> bool:
        """Valider une adresse IP"""
        try:
            ipaddress.ip_address(ip)
            return True
        except:
            return False
    
    def _validate_domain(self, domain: str) -> bool:
        """Valider un nom de domaine"""
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
        return bool(re.match(pattern, domain))
    
    def _check_port_available(self, host: str, port: int) -> bool:
        """Vérifier si un port est disponible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result != 0
        except:
            return True
    
    def _validate_network_config(self, config: dict) -> bool:
        """Valider une configuration réseau complète"""
        # Valider IP
        if not self._validate_ip(config['bind_address']):
            return False
        
        # Valider port
        if not 1024 <= config['port'] <= 65535:
            return False
        
        # Valider domaine si activé
        if config.get('enable_custom_domain'):
            if not self._validate_domain(config.get('custom_domain', '')):
                return False
        
        return True
    
    def _get_default_rules(self) -> List[Dict]:
        """Obtenir règles pare-feu par défaut"""
        return [
            {
                'name': 'Allow localhost',
                'action': 'ALLOW',
                'protocol': 'TCP',
                'source': '127.0.0.1',
                'destination': 'ANY',
                'port': 'ANY'
            },
            {
                'name': 'Block all external',
                'action': 'BLOCK',
                'protocol': 'ANY',
                'source': '0.0.0.0/0',
                'destination': 'ANY',
                'port': 'ANY'
            }
        ]
    
    def _render_add_firewall_rule(self, rules: list):
        """Interface pour ajouter une règle pare-feu"""
        st.markdown("**Nouvelle règle:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            rule_name = st.text_input("Nom de la règle")
            action = st.selectbox("Action", ["ALLOW", "BLOCK"])
            protocol = st.selectbox("Protocole", ["TCP", "UDP", "ANY"])
        
        with col2:
            source = st.text_input("IP source", value="0.0.0.0/0")
            destination = st.text_input("IP destination", value="ANY")
            port = st.text_input("Port", value="ANY")
        
        if st.button("Ajouter règle", type="primary"):
            if rule_name:
                new_rule = {
                    'name': rule_name,
                    'action': action,
                    'protocol': protocol,
                    'source': source,
                    'destination': destination,
                    'port': port
                }
                
                rules.append(new_rule)
                config_manager.set('network.firewall_rules', rules)
                st.success("✅ Règle ajoutée")
                st.rerun()
            else:
                st.error("Nom de règle requis")
    
    def _ping_host(self, host: str) -> dict:
        """Effectuer un ping"""
        import subprocess
        import time
        
        try:
            start_time = time.time()
            
            # Windows ping
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', host],
                capture_output=True,
                text=True
            )
            
            elapsed = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                return {'success': True, 'time': f"{elapsed:.1f}"}
            else:
                return {'success': False, 'error': 'Pas de réponse'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _test_port(self, host: str, port: int) -> bool:
        """Tester si un port est ouvert"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _get_detailed_network_info(self) -> dict:
        """Obtenir infos réseau détaillées"""
        info = {}
        
        try:
            for iface in netifaces.interfaces():
                iface_info = {}
                addrs = netifaces.ifaddresses(iface)
                
                # IPv4
                if netifaces.AF_INET in addrs:
                    ipv4 = addrs[netifaces.AF_INET][0]
                    iface_info['IPv4'] = ipv4['addr']
                    iface_info['Netmask'] = ipv4.get('netmask', 'N/A')
                
                # MAC
                if netifaces.AF_LINK in addrs:
                    iface_info['MAC'] = addrs[netifaces.AF_LINK][0]['addr']
                
                if iface_info:
                    info[iface] = iface_info
                    
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def _get_routing_table(self) -> list:
        """Obtenir table de routage"""
        # TODO: Implémenter pour Windows
        return []
    
    def _get_active_connections(self) -> list:
        """Obtenir connexions actives"""
        connections = []
        
        try:
            import psutil
            for conn in psutil.net_connections():
                if conn.status == 'ESTABLISHED':
                    connections.append({
                        'Local': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'Remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                        'Status': conn.status,
                        'PID': conn.pid
                    })
        except:
            pass
        
        return connections
    
    def _generate_diagnostic_report(self) -> str:
        """Générer rapport diagnostic complet"""
        report = f"""
RAPPORT DIAGNOSTIC RÉSEAU
========================
Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INTERFACES RÉSEAU:
{self._format_dict(self._get_detailed_network_info())}

CONFIGURATION ACTUELLE:
{self._format_dict(config_manager.get_section('network'))}

CONNEXIONS ACTIVES:
{len(self._get_active_connections())} connexions établies

TESTS EFFECTUÉS:
- Ping localhost: {'OK' if self._ping_host('localhost')['success'] else 'ÉCHEC'}
- Port 8501 disponible: {'OUI' if self._check_port_available('localhost', 8501) else 'NON'}
"""
        return report
    
    def _format_dict(self, d: dict, indent: int = 0) -> str:
        """Formater dictionnaire pour affichage"""
        result = []
        for key, value in d.items():
            if isinstance(value, dict):
                result.append(f"{'  ' * indent}{key}:")
                result.append(self._format_dict(value, indent + 1))
            else:
                result.append(f"{'  ' * indent}{key}: {value}")
        return '\n'.join(result)# Composant UI pour la configuration réseau 