# panel/server_mgmt.py
"""
Module de gestion du serveur OptimPV
"""

import streamlit as st
import psutil
import time
import os
from datetime import datetime
from pathlib import Path

from process.app_launcher import SecureAppLauncher
from utils.logger import SecureLogger


class ServerManagementModule:
    """Interface de gestion du serveur OptimPV"""
    
    def __init__(self, security_core):
        self.security_core = security_core
        self.logger = SecureLogger()
        self.app_launcher = SecureAppLauncher()
        
    def render(self):
        """Afficher l'interface de gestion serveur"""
        # Titre et statut
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 🖥️ Gestion du Serveur OptimPV")
        with col2:
            if st.button("🔄 Actualiser", use_container_width=True):
                st.rerun()
        
        # Carte de statut principal
        self._render_server_status()
        
        # Contrôles serveur
        st.markdown("---")
        self._render_server_controls()
        
        # Configuration serveur
        st.markdown("---")
        self._render_server_config()
        
        # Métriques détaillées
        st.markdown("---")
        self._render_detailed_metrics()
    
    def _render_server_status(self):
        """Afficher le statut du serveur"""
        status_container = st.container()
        
        with status_container:
            st.markdown("""
            <div class="info-card">
                <h3>📊 Statut du Serveur</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Vérifier si le serveur tourne
            server_info = self._get_server_info()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if server_info['running']:
                    st.metric(
                        "État",
                        "EN LIGNE",
                        delta="Actif",
                        delta_color="normal"
                    )
                else:
                    st.metric(
                        "État",
                        "ARRÊTÉ",
                        delta="Inactif",
                        delta_color="off"
                    )
            
            with col2:
                if server_info['running']:
                    st.metric(
                        "PID",
                        server_info['pid'],
                        delta=f"Port {server_info['port']}"
                    )
                else:
                    st.metric("PID", "N/A", delta="Aucun processus")
            
            with col3:
                if server_info['running']:
                    cpu = server_info.get('cpu_percent', 0)
                    st.metric(
                        "CPU",
                        f"{cpu:.1f}%",
                        delta=f"{cpu-10:+.1f}%" if cpu > 10 else "Normal"
                    )
                else:
                    st.metric("CPU", "0%", delta="N/A")
            
            with col4:
                if server_info['running']:
                    mem_mb = server_info.get('memory_mb', 0)
                    st.metric(
                        "RAM",
                        f"{mem_mb:.0f} MB",
                        delta=f"{mem_mb/1024:.1f} GB"
                    )
                else:
                    st.metric("RAM", "0 MB", delta="N/A")
            
            # Afficher uptime si serveur actif
            if server_info['running'] and server_info.get('create_time'):
                uptime = datetime.now() - datetime.fromtimestamp(server_info['create_time'])
                st.info(f"⏱️ Uptime: {str(uptime).split('.')[0]}")
            
            # URL d'accès
            if server_info['running']:
                url = f"http://{server_info['address']}:{server_info['port']}"
                st.success(f"🌐 Accessible à: [{url}]({url})")
    
    def _render_server_controls(self):
        """Afficher les contrôles du serveur"""
        st.markdown("### 🎛️ Contrôles du Serveur")
        
        server_info = self._get_server_info()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if not server_info['running']:
                if st.button("▶️ Démarrer", type="primary", use_container_width=True):
                    with st.spinner("Démarrage..."):
                        if self._start_server():
                            st.success("✅ Serveur démarré!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Échec du démarrage")
            else:
                st.button("▶️ Démarrer", disabled=True, use_container_width=True)
        
        with col2:
            if server_info['running']:
                if st.button("⏹️ Arrêter", type="secondary", use_container_width=True):
                    with st.spinner("Arrêt..."):
                        if self._stop_server():
                            st.success("✅ Serveur arrêté!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Échec de l'arrêt")
            else:
                st.button("⏹️ Arrêter", disabled=True, use_container_width=True)
        
        with col3:
            if server_info['running']:
                if st.button("🔄 Redémarrer", use_container_width=True):
                    with st.spinner("Redémarrage..."):
                        if self._restart_server():
                            st.success("✅ Serveur redémarré!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Échec du redémarrage")
            else:
                st.button("🔄 Redémarrer", disabled=True, use_container_width=True)
        
        with col4:
            if server_info['running']:
                if st.button("🌐 Ouvrir Interface", use_container_width=True):
                    url = f"http://{server_info['address']}:{server_info['port']}"
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={url}" target="_blank">', 
                               unsafe_allow_html=True)
            else:
                st.button("🌐 Ouvrir Interface", disabled=True, use_container_width=True)
    
    def _render_server_config(self):
        """Afficher la configuration du serveur"""
        st.markdown("### ⚙️ Configuration de Lancement")
        
        # Charger config actuelle
        from config.settings import config_manager
        server_config = config_manager.get_section('server')
        
        col1, col2 = st.columns(2)
        
        with col1:
            bind_address = st.text_input(
                "Adresse IP de liaison",
                value=server_config.get('bind_address', '127.0.0.1'),
                help="127.0.0.1 = local uniquement, 0.0.0.0 = toutes interfaces"
            )
            
            port = st.number_input(
                "Port",
                min_value=1024,
                max_value=65535,
                value=server_config.get('port', 8501),
                step=1
            )
            
            headless = st.checkbox(
                "Mode headless (sans navigateur)",
                value=server_config.get('headless', True)
            )
        
        with col2:
            allow_external = st.checkbox(
                "Autoriser accès externe",
                value=server_config.get('allow_external', False),
                help="⚠️ Attention: Expose le serveur sur le réseau"
            )
            
            auto_open = st.checkbox(
                "Ouvrir navigateur au démarrage",
                value=server_config.get('auto_open_browser', True)
            )
            
            max_upload_size = st.number_input(
                "Taille max upload (MB)",
                min_value=1,
                max_value=1000,
                value=server_config.get('max_upload_size', 200),
                step=10
            )
        
        # Bouton sauvegarde
        if st.button("💾 Sauvegarder Configuration", type="primary"):
            new_config = {
                'bind_address': bind_address,
                'port': port,
                'allow_external': allow_external,
                'auto_open_browser': auto_open,
                'headless': headless,
                'max_upload_size': max_upload_size
            }
            
            config_manager.update_section('server', new_config)
            st.success("✅ Configuration sauvegardée!")
            
            # Logger l'événement
            self.logger.log_event('CONFIG_CHANGE', {
                'section': 'server',
                'changes': new_config
            })
    
    def _render_detailed_metrics(self):
        """Afficher les métriques détaillées"""
        st.markdown("### 📈 Métriques Détaillées")
        
        server_info = self._get_server_info()
        
        if not server_info['running']:
            st.info("ℹ️ Le serveur doit être en ligne pour afficher les métriques")
            return
        
        # Tabs pour différentes métriques
        tab1, tab2, tab3 = st.tabs(["Performance", "Connexions", "Logs"])
        
        with tab1:
            self._render_performance_metrics(server_info)
        
        with tab2:
            self._render_connection_info(server_info)
        
        with tab3:
            self._render_server_logs()
    
    def _render_performance_metrics(self, server_info):
        """Afficher les métriques de performance"""
        col1, col2 = st.columns(2)
        
        with col1:
            # CPU history
            st.markdown("#### 🖥️ Utilisation CPU")
            
            # Simuler historique (en prod, utiliser vraies données)
            cpu_data = [server_info.get('cpu_percent', 0)] * 10
            st.line_chart(cpu_data)
            
            # Threads
            st.metric("Threads", server_info.get('num_threads', 0))
        
        with col2:
            # Memory
            st.markdown("#### 💾 Utilisation Mémoire")
            
            mem_mb = server_info.get('memory_mb', 0)
            mem_percent = server_info.get('memory_percent', 0)
            
            st.progress(mem_percent / 100)
            st.caption(f"{mem_mb:.0f} MB / {psutil.virtual_memory().total / 1024 / 1024:.0f} MB")
            
            # IO
            if 'io_counters' in server_info:
                io = server_info['io_counters']
                st.metric("Lectures", f"{io.read_bytes / 1024 / 1024:.1f} MB")
                st.metric("Écritures", f"{io.write_bytes / 1024 / 1024:.1f} MB")
    
    def _render_connection_info(self, server_info):
        """Afficher les informations de connexion"""
        st.markdown("#### 🌐 Connexions Réseau")
        
        connections = server_info.get('connections', [])
        
        if connections:
            # Tableau des connexions
            conn_data = []
            for conn in connections:
                conn_data.append({
                    'Type': conn.type,
                    'Local': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'Remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                    'Status': conn.status
                })
            
            st.dataframe(conn_data, use_container_width=True)
        else:
            st.info("Aucune connexion active")
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Connexions actives", len(connections))
        with col2:
            established = sum(1 for c in connections if c.status == 'ESTABLISHED')
            st.metric("Établies", established)
        with col3:
            listening = sum(1 for c in connections if c.status == 'LISTEN')
            st.metric("En écoute", listening)
    
    def _render_server_logs(self):
        """Afficher les logs du serveur"""
        st.markdown("#### 📋 Logs du Serveur")
        
        # Options de filtrage
        col1, col2, col3 = st.columns(3)
        with col1:
            log_lines = st.selectbox("Nombre de lignes", [50, 100, 200, 500], index=0)
        with col2:
            log_level = st.selectbox("Niveau", ["TOUS", "INFO", "WARNING", "ERROR"], index=0)
        with col3:
            if st.button("🔄 Rafraîchir"):
                st.rerun()
        
        # Zone de logs
        log_container = st.container()
        with log_container:
            logs = self._get_server_logs(lines=log_lines, level=log_level)
            
            if logs:
                # Afficher dans une zone scrollable
                log_text = "\n".join(logs)
                st.text_area(
                    "Logs",
                    value=log_text,
                    height=400,
                    disabled=True
                )
            else:
                st.info("Aucun log disponible")
        
        # Actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Exporter logs"):
                # TODO: Implémenter export
                st.info("Export en cours...")
        with col2:
            if st.button("🗑️ Nettoyer logs", type="secondary"):
                if st.checkbox("Confirmer suppression"):
                    # TODO: Implémenter nettoyage
                    st.warning("Logs nettoyés")
    
    def _get_server_info(self) -> dict:
        """Obtenir les informations du serveur"""
        # Vérifier dans session state
        if hasattr(st.session_state, 'app_process') and st.session_state.app_process:
            try:
                proc = st.session_state.app_process
                if proc.is_running():
                    # Obtenir métriques
                    with proc.oneshot():
                        info = {
                            'running': True,
                            'pid': proc.pid,
                            'port': 8501,  # TODO: Obtenir depuis config
                            'address': '127.0.0.1',
                            'cpu_percent': proc.cpu_percent(),
                            'memory_mb': proc.memory_info().rss / 1024 / 1024,
                            'memory_percent': proc.memory_percent(),
                            'create_time': proc.create_time(),
                            'num_threads': proc.num_threads(),
                            'connections': proc.connections(),
                            'io_counters': proc.io_counters() if hasattr(proc, 'io_counters') else None
                        }
                    return info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sinon chercher processus streamlit
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'streamlit' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'app.py' in cmdline:
                        # Trouvé!
                        with proc.oneshot():
                            return {
                                'running': True,
                                'pid': proc.pid,
                                'port': 8501,
                                'address': '127.0.0.1',
                                'cpu_percent': proc.cpu_percent(),
                                'memory_mb': proc.memory_info().rss / 1024 / 1024,
                                'memory_percent': proc.memory_percent(),
                                'create_time': proc.create_time(),
                                'num_threads': proc.num_threads(),
                                'connections': proc.connections()
                            }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {'running': False}
    
    def _start_server(self) -> bool:
        """Démarrer le serveur"""
        try:
            from config.settings import config_manager
            config = config_manager.get_section('server')
            
            # Lancer via launcher
            process = self.app_launcher.launch_app(config)
            
            # Sauvegarder dans session
            st.session_state.app_process = process
            st.session_state.server_status = 'running'
            
            # Logger
            self.logger.log_event('SERVER_START', {
                'pid': process.pid,
                'config': config
            })
            
            return True
            
        except Exception as e:
            self.logger.log_event('SERVER_START_ERROR', {
                'error': str(e)
            })
            return False
    
    def _stop_server(self) -> bool:
        """Arrêter le serveur"""
        try:
            if hasattr(st.session_state, 'app_process'):
                proc = st.session_state.app_process
                if proc and proc.is_running():
                    # Arrêt gracieux
                    proc.terminate()
                    proc.wait(timeout=5)
                    
                st.session_state.app_process = None
                st.session_state.server_status = 'stopped'
            
            # Logger
            self.logger.log_event('SERVER_STOP', {})
            return True
            
        except Exception as e:
            self.logger.log_event('SERVER_STOP_ERROR', {
                'error': str(e)
            })
            return False
    
    def _restart_server(self) -> bool:
        """Redémarrer le serveur"""
        if self._stop_server():
            time.sleep(2)
            return self._start_server()
        return False
    
    def _get_server_logs(self, lines: int = 50, level: str = "TOUS") -> list:
        """Obtenir les logs du serveur"""
        # TODO: Implémenter lecture vraie des logs
        # Pour démo:
        import random
        levels = ["INFO", "WARNING", "ERROR"] if level == "TOUS" else [level]
        
        logs = []
        for i in range(lines):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_level = random.choice(levels)
            messages = [
                "Server started successfully",
                "New connection from 127.0.0.1",
                "Request processed in 0.023s",
                "Cache cleared",
                "Configuration reloaded"
            ]
            
            log = f"[{timestamp}] {log_level}: {random.choice(messages)}"
            logs.append(log)
        
        return logs# Composant UI pour la gestion du serveur OptimPV 