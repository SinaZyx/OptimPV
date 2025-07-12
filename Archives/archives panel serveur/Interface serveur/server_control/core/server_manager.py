#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Gestionnaire de Serveur
=================================

Module dédié à la gestion du serveur OptimPV.
"""

import streamlit as st
import subprocess
import psutil
import time
import os
import requests
import sys
from pathlib import Path
from .utils import load_network_config, log_message


class OptimPVServerManager:
    """Gestionnaire du serveur OptimPV"""
    
    def __init__(self):
        self.process = None
        self.config = load_network_config()
        # Forcer le port 8502 pour l'application OptimPV principale (différent du panneau de contrôle)
        self.config['port'] = 8502
        # Utiliser AppData pour les logs
        appdata_dir = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'OptimPV')
        os.makedirs(appdata_dir, exist_ok=True)
        self.log_file = os.path.join(appdata_dir, "optimpv_server.log")
        
    def is_server_running(self):
        """Vérifie si le serveur OptimPV est déjà en cours d'exécution"""
        try:
            # Rechargement de la configuration au cas où elle aurait changé
            self.config = load_network_config()
            
            # Liste des ports à vérifier SAUF le port du panneau de contrôle
            current_port = int(os.environ.get('STREAMLIT_SERVER_PORT', 8504))
            
            ports_to_check = [
                8502,  # Port principal pour OptimPV
                8501, 8505, 8506, 8507  # Ports alternatifs courants
            ]
            
            # Retirer le port actuel du panneau de contrôle (8504)
            if current_port in ports_to_check:
                ports_to_check.remove(current_port)
            
            # Supprimer les doublons et trier
            ports_to_check = list(set(ports_to_check))
            
            for port in ports_to_check:
                try:
                    # Vérifier si le port est occupé avec une requête HTTP
                    response = requests.get(
                        f"http://{self.config['ip']}:{port}", 
                        timeout=2,
                        headers={'User-Agent': 'OptimPV-Control-Panel'}
                    )
                    
                    # Vérifier que c'est bien une app Streamlit (OptimPV)
                    if response.status_code == 200:
                        content = response.text.lower()
                        # Vérifier que ce n'est PAS le panneau de contrôle
                        if 'streamlit' in content and 'control panel' not in content and 'panneau de contrôle' not in content:
                            # Mettre à jour la configuration avec le port trouvé
                            if port != self.config['port']:
                                log_message(f"Serveur OptimPV trouvé sur port {port} (au lieu de {self.config['port']})")
                                self.config['port'] = port
                            return True
                            
                except requests.exceptions.RequestException:
                    # Ce port ne répond pas, essayer le suivant
                    continue
                    
            return False
            
        except Exception as e:
            log_message(f"Erreur inattendue lors de la vérification: {e}")
            return False
    
    def get_server_process(self):
        """Trouve le processus du serveur OptimPV (excluant le panneau de contrôle)"""
        current_pid = os.getpid()  # PID du panneau de contrôle actuel
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Ignorer le processus actuel (panneau de contrôle)
                if proc.info['pid'] == current_pid:
                    continue
                    
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'])
                    # Chercher launcher.py ou app.py mais pas server_control_panel.py
                    if ('streamlit' in cmdline and 
                        ('launcher.py' in cmdline or 'app.py' in cmdline) and
                        'server_control_panel' not in cmdline):
                        return proc
            except:
                continue
        return None
    
    def start_server(self):
        """Démarre le serveur OptimPV"""
        if self.is_server_running():
            return False, "Le serveur OptimPV est déjà en cours d'exécution"
        
        try:
            # Aller à la racine du projet (4 niveaux au-dessus)
            project_root = Path(__file__).parent.parent.parent.parent
            launcher_path = project_root / "Interface serveur" / "launcher.py"
            app_path = project_root / "app.py"
            
            # Vérifier que le launcher existe dans Interface serveur
            if not launcher_path.exists():
                return False, f"Fichier launcher.py non trouvé dans {project_root / 'Interface serveur'}"
            
            # Vérifier que app.py existe à la racine
            if not app_path.exists():
                return False, f"Fichier app.py non trouvé dans {project_root}"
            
            # Commande pour lancer le serveur depuis la racine
            cmd = [
                sys.executable, str(launcher_path)  # Chemin complet vers launcher.py
            ]
            
            log_message(f"Tentative de démarrage du serveur avec: {' '.join(cmd)}")
            log_message(f"Répertoire de travail: {project_root}")
            
            # Démarrer le processus en arrière-plan depuis la racine du projet
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capturer stderr séparément
                text=True,
                cwd=str(project_root)  # Exécuter depuis la racine du projet
            )
            
            log_message(f"Processus lancé avec PID: {self.process.pid}")
            
            # Attendre un peu plus longtemps et vérifier en continu
            for i in range(10):  # 10 secondes max
                time.sleep(1)
                
                # Vérifier si le processus est encore vivant
                if self.process.poll() is not None:
                    # Le processus s'est terminé
                    stdout, stderr = self.process.communicate()
                    error_msg = f"Le processus s'est terminé prématurément (code: {self.process.returncode})"
                    if stderr:
                        error_msg += f"\nErreur: {stderr.strip()}"
                    if stdout:
                        error_msg += f"\nSortie: {stdout.strip()}"
                    
                    log_message(f"Erreur de démarrage: {error_msg}")
                    return False, error_msg
                
                # Vérifier si le serveur répond
                if self.is_server_running():
                    log_message(f"Serveur OptimPV démarré avec succès - PID: {self.process.pid}")
                    return True, f"Serveur démarré avec succès sur {self.config['ip']}:{self.config['port']}"
                
                log_message(f"Tentative {i+1}/10 - Serveur pas encore accessible...")
            
            # Si on arrive ici, le serveur ne répond pas après 10 secondes
            # Vérifier s'il y a des erreurs dans la sortie
            try:
                stdout, stderr = self.process.communicate(timeout=1)
                if stderr:
                    error_details = f"Erreurs détectées: {stderr.strip()}"
                else:
                    error_details = "Le serveur ne répond pas après 10 secondes"
                
                if stdout:
                    error_details += f"\nSortie: {stdout.strip()}"
                    
            except subprocess.TimeoutExpired:
                error_details = "Le serveur semble démarrer mais ne répond pas encore"
            
            log_message(f"Timeout de démarrage: {error_details}")
            return False, f"Timeout: {error_details}"
                
        except Exception as e:
            error_msg = f"Erreur lors du lancement: {str(e)}"
            log_message(error_msg)
            return False, error_msg
    
    def stop_server(self):
        """Arrête le serveur OptimPV"""
        try:
            # Trouver et arrêter le processus
            proc = self.get_server_process()
            if proc:
                proc.terminate()
                time.sleep(2)
                
                if proc.is_running():
                    proc.kill()
                
                log_message("Serveur OptimPV arrêté")
                return True, "Serveur arrêté avec succès"
            else:
                return False, "Aucun serveur OptimPV en cours d'exécution"
                
        except Exception as e:
            return False, f"Erreur lors de l'arrêt: {str(e)}"
    
    def get_server_url(self):
        """Retourne l'URL d'accès au serveur OptimPV principal"""
        # Toujours utiliser le port 8502 pour l'application OptimPV principale
        return f"http://{self.config['ip']}:8502"


def show_server_control_tab(server_manager, server_running):
    """Onglet de contrôle du serveur"""
    
    st.header("🖥️ Contrôle du Serveur OptimPV")
    
    # État actuel du serveur
    if server_running:
        st.markdown("""
        <div class="server-status-running">
            <h3>✅ Serveur OptimPV EN LIGNE</h3>
            <p>Le serveur d'optimisation photovoltaïque est actuellement en cours d'exécution.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="server-status-stopped">
            <h3>⛔ Serveur OptimPV ARRÊTÉ</h3>
            <p>Le serveur d'optimisation photovoltaïque n'est pas en cours d'exécution.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Contrôles du serveur
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not server_running:
            if st.button("🚀 Démarrer le Serveur", type="primary", use_container_width=True, key="start_server_btn"):
                with st.spinner("Démarrage du serveur en cours..."):
                    success, message = server_manager.start_server()
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.button("🚀 Serveur Déjà Démarré", disabled=True, use_container_width=True, key="server_already_started_btn")
    
    with col2:
        if server_running:
            if st.button("⏹️ Arrêter le Serveur", type="secondary", use_container_width=True, key="stop_server_btn"):
                with st.spinner("Arrêt du serveur en cours..."):
                    success, message = server_manager.stop_server()
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.button("⏹️ Serveur Déjà Arrêté", disabled=True, use_container_width=True, key="server_already_stopped_btn")
    
    with col3:
        if server_running:
            server_url = server_manager.get_server_url()
            if st.button("🌐 Accéder à OptimPV", type="primary", use_container_width=True, key="access_optimpv_btn"):
                st.balloons()
                st.markdown(f"""
                ### 🎉 Accès à l'Application OptimPV
                
                L'application OptimPV principale est accessible à l'adresse suivante :
                
                **[🔗 Ouvrir OptimPV]({server_url})**
                
                > 🌞 Cliquez sur le lien pour accéder à votre application d'optimisation photovoltaïque principale.
                
                ---
                
                **ℹ️ Informations sur les ports :**
                - **Application OptimPV** : {server_url} (Interface principale d'optimisation)
                - **Panneau de Contrôle** : http://127.0.0.1:8504 (Interface d'administration actuelle)
                
                Les deux applications utilisent des ports différents pour éviter les conflits.
                """)
        else:
            st.button("🌐 Serveur Non Disponible", disabled=True, use_container_width=True, key="server_not_available_btn")
    
    # Informations techniques
    st.markdown("---")
    st.subheader("📋 Informations Techniques")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Configuration Réseau:**")
        config = server_manager.config
        st.code(f"""
IP: {config['ip']}
Port OptimPV: 8502
Port Panneau: 8504
URL OptimPV: {server_manager.get_server_url()}
Accès externe: {'Oui' if config.get('external_access') else 'Non'}
        """)
    
    with col2:
        st.write("**État du Système:**")
        proc = server_manager.get_server_process()
        if proc:
            try:
                st.code(f"""
PID: {proc.pid}
CPU: {proc.cpu_percent():.1f}%
Mémoire: {proc.memory_info().rss / 1024 / 1024:.1f} MB
Statut: En cours d'exécution
                """)
            except:
                st.code("Processus détecté mais informations non disponibles")
        else:
            st.code("Aucun processus OptimPV détecté") 