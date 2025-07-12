#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Panneau de Contrôle Serveur
=====================================

Interface de contrôle pour gérer le serveur OptimPV :
- Lancement/arrêt du serveur
- Monitoring en temps réel
- Logs du serveur
- Administration réseau
- Accès direct à l'application
"""

import streamlit as st
import subprocess
import psutil
import time
import os
import requests
from datetime import datetime
import sys
from pathlib import Path

# Ajouter le chemin vers la racine du projet pour importer admin_config
project_root = Path(__file__).parent.parent.parent.parent  # Remonter de 4 niveaux
interface_serveur_path = project_root / "Interface serveur"
sys.path.insert(0, str(interface_serveur_path))

# Import du module d'administration
try:
    from admin_config import NetworkAdminConfig
    ADMIN_MODULE_AVAILABLE = True
except ImportError:
    ADMIN_MODULE_AVAILABLE = False

# Ajouter le chemin du module de sécurité
security_path = os.path.join(os.path.dirname(__file__), '..', '..', 'security')
sys.path.append(security_path)

# Essayer plusieurs méthodes d'import pour hardware_protection
try:
    # Méthode 1: Import depuis le dossier security organisé
    from hardware_protection import require_license, LicenseManager  # type: ignore
    PROTECTION_ENABLED = True
except ImportError:
    try:
        # Méthode 2: Import relatif depuis le package security
        from server_control.security.hardware_protection import require_license, LicenseManager
        PROTECTION_ENABLED = True
    except ImportError:
        try:
            # Méthode 3: Import absolu avec vérification de type
            import importlib.util
            security_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'security', 'hardware_protection.py')
            if os.path.exists(security_file_path):
                spec = importlib.util.spec_from_file_location("hardware_protection", security_file_path)
                if spec is not None and spec.loader is not None:
                    hardware_protection = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(hardware_protection)
                    require_license = hardware_protection.require_license
                    LicenseManager = hardware_protection.LicenseManager
                    PROTECTION_ENABLED = True
                else:
                    raise ImportError("Spec de module invalide")
            else:
                raise ImportError("Module hardware_protection non trouvé")
        except ImportError:
            # Si le module n'est pas disponible, continuer sans protection
            PROTECTION_ENABLED = False
            def require_license(func):
                return func

def normalize_mac_address(mac_str):
    """
    Normalise une adresse MAC vers le format standard XX:XX:XX:XX:XX:XX
    
    Args:
        mac_str (str): Adresse MAC dans différents formats
        
    Returns:
        str: Adresse MAC normalisée ou None si invalide
    """
    if not mac_str:
        return None
    
    # Supprimer les espaces et convertir en minuscules
    mac_clean = mac_str.strip().lower()
    
    # Supprimer tous les séparateurs possibles
    mac_clean = mac_clean.replace(':', '').replace('-', '').replace('.', '').replace(' ', '')
    
    # Vérifier que c'est bien 12 caractères hexadécimaux
    if len(mac_clean) != 12:
        return None
    
    try:
        # Vérifier que tous les caractères sont hexadécimaux
        int(mac_clean, 16)
    except ValueError:
        return None
    
    # Reformater avec des deux-points
    formatted_mac = ':'.join([mac_clean[i:i+2] for i in range(0, 12, 2)])
    
    # Convertir en majuscules pour la cohérence
    return formatted_mac.upper()


class OptimPVServerManager:
    """Gestionnaire du serveur OptimPV"""
    
    def __init__(self):
        self.process = None
        self.config = self._load_network_config()
        self.log_file = "optimpv_server.log"
        
    def _load_network_config(self):
        """Charge la configuration réseau"""
        if ADMIN_MODULE_AVAILABLE:
            try:
                admin_config = NetworkAdminConfig()
                return admin_config.get_network_config()
            except:
                pass
        
        # Configuration par défaut
        return {
            "ip": "127.0.0.1",
            "port": 8502,  # Port par défaut pour l'application principale
            "external_access": False
        }
    
    def is_server_running(self):
        """Vérifie si le serveur OptimPV est déjà en cours d'exécution"""
        try:
            # Rechargement de la configuration au cas où elle aurait changé
            self.config = self._load_network_config()
            
            # Liste des ports à vérifier SAUF le port du panneau de contrôle
            current_port = int(os.environ.get('STREAMLIT_SERVER_PORT', 8501))
            
            ports_to_check = [
                self.config['port'],  # Port configuré
                8502, 8504, 8505, 8506, 8507  # Ports alternatifs courants
            ]
            
            # Retirer le port actuel du panneau de contrôle
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
                                self._log(f"Serveur OptimPV trouvé sur port {port} (au lieu de {self.config['port']})")
                                self.config['port'] = port
                            return True
                            
                except requests.exceptions.RequestException:
                    # Ce port ne répond pas, essayer le suivant
                    continue
                    
            return False
            
        except Exception as e:
            self._log(f"Erreur inattendue lors de la vérification: {e}")
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
                        'server_control_panel.py' not in cmdline):
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
            
            self._log(f"Tentative de démarrage du serveur avec: {' '.join(cmd)}")
            self._log(f"Répertoire de travail: {project_root}")
            
            # Démarrer le processus en arrière-plan depuis la racine du projet
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capturer stderr séparément
                text=True,
                cwd=str(project_root)  # Exécuter depuis la racine du projet
            )
            
            self._log(f"Processus lancé avec PID: {self.process.pid}")
            
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
                    
                    self._log(f"Erreur de démarrage: {error_msg}")
                    return False, error_msg
                
                # Vérifier si le serveur répond
                if self.is_server_running():
                    self._log(f"Serveur OptimPV démarré avec succès - PID: {self.process.pid}")
                    return True, f"Serveur démarré avec succès sur {self.config['ip']}:{self.config['port']}"
                
                self._log(f"Tentative {i+1}/10 - Serveur pas encore accessible...")
            
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
            
            self._log(f"Timeout de démarrage: {error_details}")
            return False, f"Timeout: {error_details}"
                
        except Exception as e:
            error_msg = f"Erreur lors du lancement: {str(e)}"
            self._log(error_msg)
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
                
                self._log("Serveur OptimPV arrêté")
                return True, "Serveur arrêté avec succès"
            else:
                return False, "Aucun serveur OptimPV en cours d'exécution"
                
        except Exception as e:
            return False, f"Erreur lors de l'arrêt: {str(e)}"
    
    def get_server_url(self):
        """Retourne l'URL d'accès au serveur OptimPV principal"""
        # Si le serveur OptimPV principal est détecté sur un autre port, utiliser ce port
        if self.is_server_running():
            return f"http://{self.config['ip']}:{self.config['port']}"
        else:
            # Sinon, retourner l'URL configurée (même si le serveur n'est pas démarré)
            return f"http://{self.config['ip']}:{self.config['port']}"
    
    def _log(self, message):
        """Ajoute une entrée au log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def get_logs(self, lines=50):
        """Récupère les dernières lignes de log"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_lines = f.readlines()
                return log_lines[-lines:] if len(log_lines) > lines else log_lines
            else:
                return ["Aucun log disponible"]
        except Exception as e:
            return [f"Erreur lecture logs: {str(e)}"]


def check_usb_access_realtime():
    """Vérification en temps réel de l'accès USB"""
    if not PROTECTION_ENABLED:
        return True, "Protection désactivée"
    
    try:
        license_manager = LicenseManager()
        check_usb_method = getattr(license_manager, 'check_usb_token', None)
        if check_usb_method:
            usb_valid, usb_message = check_usb_method()
            return usb_valid, usb_message
        return False, "Méthode USB non disponible"
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def main_control_panel():
    """Interface de contrôle principale avec gestion conditionnelle des permissions"""
    
    st.set_page_config(
        page_title="OptimPV - Server Control Panel",
        page_icon="🌞",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Vérifier la licence/clé USB pour déterminer les permissions
    has_full_access = False
    license_status = "Non vérifié"
    usb_access = False
    
    if PROTECTION_ENABLED:
        try:
            license_manager = LicenseManager()
            
            # Vérifier d'abord le token USB (priorité) si la méthode existe
            check_usb_method = getattr(license_manager, 'check_usb_token', None)
            if check_usb_method:
                usb_valid, usb_message = check_usb_method()
                if usb_valid:
                    has_full_access = True
                    usb_access = True
                    license_status = f"🔑 {usb_message}"
                else:
                    # Vérifier ensuite la licence classique
                    authorized, message = license_manager.check_license()
                    if authorized:
                        has_full_access = True
                        usb_access = False
                        license_status = f"✅ {message}"
                    else:
                        has_full_access = False
                        usb_access = False
                        license_status = f"❌ {message}"
            else:
                # Seulement la licence classique si pas de support USB
                authorized, message = license_manager.check_license()
                if authorized:
                    has_full_access = True
                    usb_access = False
                    license_status = f"✅ {message}"
                else:
                    has_full_access = False
                    usb_access = False
                    license_status = f"❌ {message}"
        except Exception as e:
            has_full_access = False
            usb_access = False
            license_status = f"❌ Erreur: {str(e)}"
    else:
        # Si la protection n'est pas activée, donner accès complet
        has_full_access = True
        usb_access = False
        license_status = "Protection désactivée"

    # Authentification globale pour accéder au panneau (seulement pour le menu démarrer si pas d'accès complet)
    if 'panel_authenticated' not in st.session_state:
        st.session_state.panel_authenticated = False

    # Si pas d'accès complet et pas authentifié au panneau, afficher seulement l'interface de contrôle serveur
    if not has_full_access and not st.session_state.panel_authenticated:
        # Interface simple sans mention de sécurité
        st.markdown("""
        <h1 style='text-align: center; color: #2E8B57;'>
            🌞 OptimPV - Server Control Panel
        </h1>
        <p style='text-align: center; font-size: 1.2em; color: #555;'>
            Interface de contrôle du serveur d'optimisation photovoltaïque
        </p>
        """, unsafe_allow_html=True)
        
        # Styles CSS intégrés
        st.markdown("""
        <style>
        .server-status-running {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .server-status-stopped {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .metric-container {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Initialisation du gestionnaire de serveur
        server_manager = OptimPVServerManager()
        server_running = server_manager.is_server_running()
        
        # Interface de contrôle serveur simple (identique à show_server_control_tab)
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
                if st.button("🚀 Démarrer le Serveur", type="primary", use_container_width=True):
                    with st.spinner("Démarrage du serveur en cours..."):
                        success, message = server_manager.start_server()
                        if success:
                            st.success(message)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.button("🚀 Serveur Déjà Démarré", disabled=True, use_container_width=True)
        
        with col2:
            if server_running:
                if st.button("⏹️ Arrêter le Serveur", type="secondary", use_container_width=True):
                    with st.spinner("Arrêt du serveur en cours..."):
                        success, message = server_manager.stop_server()
                        if success:
                            st.success(message)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                st.button("⏹️ Serveur Déjà Arrêté", disabled=True, use_container_width=True)
        
        with col3:
            if server_running:
                server_url = server_manager.get_server_url()
                if st.button("🌐 Accéder à OptimPV", type="primary", use_container_width=True):
                    st.balloons()
                    st.markdown(f"""
                    ### 🎉 Accès à l'Application OptimPV
                    
                    L'application OptimPV principale est accessible à l'adresse suivante :
                    
                    **[🔗 Ouvrir OptimPV]({server_url})**
                    
                    > 🌞 Cliquez sur le lien pour accéder à votre application d'optimisation photovoltaïque principale.
                    """)
            else:
                st.button("🌐 Serveur Non Disponible", disabled=True, use_container_width=True)
        
        # Informations techniques
        st.markdown("---")
        st.subheader("📋 Informations Techniques")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Configuration Réseau:**")
            config = server_manager.config
            st.code(f"""
IP: {config['ip']}
Port: {config['port']}
URL: {server_manager.get_server_url()}
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
        
        # Sidebar simple pour les utilisateurs sans accès complet
        with st.sidebar:
            st.header("📊 État du Système")
            
            if server_running:
                st.success("🟢 Serveur OptimPV Actif")
            else:
                st.error("🔴 Serveur OptimPV Inactif")

            # Bouton de vérification USB pour obtenir l'accès complet
            st.markdown("---")
            st.subheader("🔑 Accès Administrateur")
            
            if st.button("🔍 Vérifier Clé USB", use_container_width=True, key="sidebar_verify_usb"):
                usb_valid, usb_message = check_usb_access_realtime()
                if usb_valid:
                    st.success(f"✅ {usb_message}")
                    st.success("🔄 Clé USB détectée ! Actualisez la page pour accéder aux fonctions avancées.")
                    if st.button("🔄 Actualiser maintenant", key="sidebar_usb_detected_refresh"):
                        st.rerun()
                else:
                    st.error(f"❌ {usb_message}")
                    st.info("💡 Insérez votre clé USB administrateur pour accéder aux fonctions avancées")
            
            # Information statique sur l'USB
            st.info("💡 Insérez votre clé USB administrateur et cliquez sur 'Vérifier Clé USB' pour accéder aux fonctions avancées")

            st.markdown("---")
            st.info("""
            **OptimPV Server Control Panel**
            
            Interface de contrôle du serveur d'optimisation photovoltaïque.
            
            🔧 Contrôle du serveur
            🌐 Accès à l'application
            """)
        
        return  # Arrêter ici si pas d'accès complet et pas authentifié

    # Interface principale (accès complet ou authentifié)
    # Bouton de déconnexion dans la sidebar si authentifié par mot de passe
    with st.sidebar:
        if not has_full_access and st.session_state.panel_authenticated:
            st.markdown("---")
            if st.button("🚪 Retour au Menu de Base", type="secondary"):
                st.session_state.panel_authenticated = False
                st.rerun()

    # Titre et description (après authentification ou avec clé USB)
    st.markdown("""
    <h1 style='text-align: center; color: #2E8B57;'>
        🌞 OptimPV - Server Control Panel
    </h1>
    <p style='text-align: center; font-size: 1.2em; color: #555;'>
        Interface de gestion et de contrôle du serveur d'optimisation photovoltaïque
    </p>
    """, unsafe_allow_html=True)

    # Afficher le statut d'accès
    if has_full_access:
        st.success(f"🔓 Accès complet autorisé - {license_status}")
    else:
        st.warning(f"🔐 Accès administrateur par mot de passe - {license_status}")

    # Styles CSS intégrés
    st.markdown("""
    <style>
    .server-status-running {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .server-status-stopped {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Initialisation du gestionnaire de serveur
    server_manager = OptimPVServerManager()
    server_running = server_manager.is_server_running()

    # Sidebar avec informations système
    with st.sidebar:
        st.header("📊 État du Système")
        
        if server_running:
            st.success("🟢 Serveur OptimPV Actif")
        else:
            st.error("🔴 Serveur OptimPV Inactif")

        # Informations sur la licence
        st.markdown("---")
        st.subheader("🔐 Statut d'Accès")
        
        if has_full_access:
            st.success("✅ Accès complet")
        else:
            st.warning("⚠️ Accès limité")
        
        st.caption(license_status)
        
        # Bouton de vérification USB en temps réel
        st.markdown("---")
        st.subheader("🔑 Vérification USB")
        
        # Information sur le fonctionnement
        st.info("""
        💡 **Fonctionnement :**
        - Cliquez sur "Vérifier USB" pour détecter votre clé administrateur
        - Si détectée, cliquez sur "Actualiser" pour accéder aux fonctions avancées
        - Aucune vérification automatique (pas de refresh permanent)
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Vérifier USB", use_container_width=True, key="main_verify_usb"):
                usb_valid, usb_message = check_usb_access_realtime()
                if usb_valid:
                    st.success(f"✅ {usb_message}")
                    # Si USB détectée et on n'avait pas accès avant, proposer de recharger
                    if not usb_access:
                        st.success("🔄 Clé USB détectée ! Actualisez la page pour accéder aux fonctions avancées.")
                        if st.button("🔄 Actualiser maintenant", key="usb_detected_refresh"):
                            st.rerun()
                else:
                    st.error(f"❌ {usb_message}")
                    # Si USB débranchée et on avait accès USB avant, informer l'utilisateur
                    if usb_access:
                        st.warning("⚠️ Clé USB non détectée. Actualisez la page si vous l'avez débranchée.")
        
        with col2:
            # Bouton d'actualisation manuelle
            if st.button("🔄 Actualiser Page", use_container_width=True, key="main_refresh"):
                st.info("Page actualisée")
                st.rerun()

        # Statut USB (sans vérification automatique)
        if usb_access:
            st.success(f"🔑 USB: Connectée au démarrage")
        else:
            st.info(f"🔒 USB: Non détectée au démarrage")

        st.markdown("---")
        st.info("""
        **OptimPV Server Control Panel**
        
        Interface de gestion du serveur d'optimisation photovoltaïque.
        
        🔧 Contrôle du serveur
        📜 Monitoring des logs
        🔧 Administration réseau
        """)

    # Interface principale avec onglets conditionnels
    if has_full_access or st.session_state.panel_authenticated:
        # Accès complet - tous les onglets
        tab1, tab2, tab3, tab4 = st.tabs([
            "🖥️ Contrôle Serveur", 
            "📜 Logs & Monitoring", 
            "🔧 Administration",
            "🔐 Licence"
        ])
        
        with tab1:
            show_server_control_tab(server_manager, server_running)
        
        with tab2:
            show_logs_monitoring_tab(server_manager)
        
        with tab3:
            show_admin_tab()
            
        with tab4:
            show_license_tab()
    else:
        # Cette section ne devrait jamais être atteinte car les utilisateurs sans accès
        # sont redirigés vers l'interface simple plus haut
        st.error("Erreur d'affichage - veuillez actualiser la page")


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
            if st.button("🚀 Démarrer le Serveur", type="primary", use_container_width=True):
                with st.spinner("Démarrage du serveur en cours..."):
                    success, message = server_manager.start_server()
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.button("🚀 Serveur Déjà Démarré", disabled=True, use_container_width=True)
    
    with col2:
        if server_running:
            if st.button("⏹️ Arrêter le Serveur", type="secondary", use_container_width=True):
                with st.spinner("Arrêt du serveur en cours..."):
                    success, message = server_manager.stop_server()
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
        else:
            st.button("⏹️ Serveur Déjà Arrêté", disabled=True, use_container_width=True)
    
    with col3:
        if server_running:
            server_url = server_manager.get_server_url()
            if st.button("🌐 Accéder à OptimPV", type="primary", use_container_width=True):
                st.balloons()
                st.markdown(f"""
                ### 🎉 Accès à l'Application OptimPV
                
                L'application OptimPV principale est accessible à l'adresse suivante :
                
                **[🔗 Ouvrir OptimPV]({server_url})**
                
                > 🌞 Cliquez sur le lien pour accéder à votre application d'optimisation photovoltaïque principale.
                
                ---
                
                **ℹ️ Note importante :**
                - **Application OptimPV** : {server_url} (Interface principale)
                - **Panneau de Contrôle** : Interface d'administration actuelle
                
                Si le lien vous redirige vers cette page, c'est que l'application principale 
                n'est pas encore démarrée ou utilise le même port.
                """)
        else:
            st.button("🌐 Serveur Non Disponible", disabled=True, use_container_width=True)
    
    # Informations techniques
    st.markdown("---")
    st.subheader("📋 Informations Techniques")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Configuration Réseau:**")
        config = server_manager.config
        st.code(f"""
IP: {config['ip']}
Port: {config['port']}
URL: {server_manager.get_server_url()}
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
    
    logs = server_manager.get_logs(lines_to_show)
    
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


def show_admin_tab():
    """Onglet d'administration"""
    
    st.header("🔧 Administration Réseau")
    
    if not ADMIN_MODULE_AVAILABLE:
        st.error("Module d'administration non disponible")
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
        
        # Formulaire de connexion admin avec ID + mot de passe (système original)
        admin_config = NetworkAdminConfig()
        
        with st.form("admin_login_form"):
            st.subheader("Connexion Administrateur")
            
            username = st.text_input("Nom d'utilisateur", value="admin", placeholder="Entrez l'identifiant administrateur")
            password = st.text_input("Mot de passe", type="password", placeholder="Entrez le mot de passe administrateur")
            
            submit_button = st.form_submit_button("Se connecter")
            
            if submit_button:
                # Authentification avec ID + mot de passe (système original)
                if admin_config.authenticate(username, password):
                    st.session_state.admin_authenticated = True
                    st.success("✅ Connexion administrateur réussie !")
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")
        
        st.markdown("---")
        st.info("**Identifiants par défaut:** admin / admin123")
        st.warning("⚠️ Changez le mot de passe par défaut après la première connexion !")
    
    else:
        # Interface d'administration complète
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.write("**Interface d'Administration**")
        
        with col2:
            if st.button("🚪 Déconnexion Admin"):
                st.session_state.admin_authenticated = False
                st.rerun()
        
        # Afficher l'interface d'administration
        admin_config = NetworkAdminConfig()
        
        # Tabs pour l'administration
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
            "🌐 Configuration Réseau",
            "🔒 Sécurité", 
            "🔐 Licences Hardware",
            "📄 Export Config"
        ])
        
        with admin_tab1:
            show_network_config_in_control_panel(admin_config)
        
        with admin_tab2:
            show_security_config_in_control_panel(admin_config)
        
        with admin_tab3:
            show_hardware_license_admin_tab(admin_config)
        
        with admin_tab4:
            show_export_config_in_control_panel(admin_config)


def show_network_config_in_control_panel(admin_config):
    """Affiche la configuration réseau dans le panneau de contrôle"""
    st.subheader("🌐 Configuration Réseau")
    
    try:
        current_config = admin_config.get_network_config()
        
        with st.form("network_config_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Paramètres de Base")
                
                new_ip = st.selectbox(
                    "Adresse IP",
                    options=["127.0.0.1", "0.0.0.0"],
                    index=0 if current_config['ip'] == "127.0.0.1" else 1,
                    help="127.0.0.1 = accès local uniquement, 0.0.0.0 = accès réseau autorisé"
                )
                
                new_port = st.number_input(
                    "Port",
                    min_value=1024,
                    max_value=65535,
                    value=current_config['port'],
                    help="Port d'écoute du serveur (évitez 8501 réservé au panneau)"
                )
                
                new_external_access = st.checkbox(
                    "Autoriser l'accès externe",
                    value=current_config['external_access'],
                    help="Permet l'accès depuis d'autres machines du réseau"
                )
            
            with col2:
                st.markdown("#### Paramètres Avancés")
                
                new_custom_domain = st.text_input(
                    "Domaine personnalisé (optionnel)",
                    value=current_config.get('custom_domain', ''),
                    help="Ex: optimpv.mondomaine.com"
                )
                
                # NOUVEAU : Configuration du mode navigateur
                st.markdown("#### 🌐 Comportement Navigateur")
                
                browser_mode = st.selectbox(
                    "Mode d'ouverture navigateur",
                    options=[
                        "headless_always", 
                        "headless_network_only", 
                        "auto_open_local"
                    ],
                    index=0,  # Par défaut headless_always
                    format_func=lambda x: {
                        "headless_always": "🔒 Toujours headless (jamais d'ouverture auto)",
                        "headless_network_only": "🌐 Headless pour accès réseau uniquement", 
                        "auto_open_local": "🖥️ Ouverture auto en local seulement"
                    }[x],
                    help="Contrôle quand le navigateur s'ouvre automatiquement"
                )
                
                force_headless_panel = st.checkbox(
                    "Forcer headless pour le panneau de contrôle",
                    value=True,
                    disabled=True,  # Toujours activé pour la sécurité
                    help="Le panneau de contrôle reste toujours en mode headless (recommandé)"
                )
                
                # Affichage des IPs autorisées
                st.markdown("#### 🔐 Sécurité")
                allowed_ips_text = st.text_area(
                    "IPs autorisées (une par ligne)",
                    value='\n'.join(current_config['allowed_ips']),
                    height=100,
                    help="Liste des adresses IP autorisées à accéder au serveur"
                )
            
            st.markdown("---")
            
            col_save, col_reset = st.columns([1, 1])
            
            with col_save:
                save_button = st.form_submit_button("💾 Sauvegarder Configuration", type="primary")
            
            with col_reset:
                reset_button = st.form_submit_button("🔄 Réinitialiser", type="secondary")
            
            if save_button:
                try:
                    # Traitement des IPs autorisées
                    new_allowed_ips = [ip.strip() for ip in allowed_ips_text.split('\n') if ip.strip()]
                    if not new_allowed_ips:
                        new_allowed_ips = ["127.0.0.1"]  # Au minimum localhost
                    
                    # Nouvelle configuration avec mode navigateur
                    new_config = {
                        'ip': new_ip,
                        'port': int(new_port),
                        'external_access': new_external_access,
                        'custom_domain': new_custom_domain.strip() if new_custom_domain and new_custom_domain.strip() else None,
                        'allowed_ips': new_allowed_ips,
                        'browser_mode': browser_mode,  # NOUVEAU
                        'force_headless_panel': force_headless_panel  # NOUVEAU
                    }
                    
                    # Validation
                    if new_port == 8501:
                        st.warning("⚠️ Le port 8501 est réservé au panneau de contrôle. Choisissez un autre port.")
                    elif admin_config.update_network_config(new_config):
                        st.success("✅ Configuration réseau sauvegardée avec succès !")
                        st.info("🔄 Redémarrez le serveur pour appliquer les changements.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la sauvegarde de la configuration")
                        
                except Exception as e:
                    st.error(f"❌ Erreur de validation: {str(e)}")
            
            if reset_button:
                try:
                    if admin_config.reset_network_config():
                        st.success("✅ Configuration réseau réinitialisée !")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la réinitialisation")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
        
        # Affichage des informations actuelles
        st.markdown("---")
        st.markdown("#### 📊 Configuration Actuelle")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Adresse IP", current_config['ip'])
            st.metric("Port", current_config['port'])
        
        with col2:
            st.metric("Accès externe", "✅ Activé" if current_config['external_access'] else "❌ Désactivé")
            st.metric("Mode navigateur", {
                "headless_always": "🔒 Toujours headless",
                "headless_network_only": "🌐 Headless réseau", 
                "auto_open_local": "🖥️ Auto local"
            }.get(current_config.get('browser_mode', 'headless_always'), "🔒 Headless"))
        
        with col3:
            domain = current_config.get('custom_domain', 'Aucun')
            st.metric("Domaine", domain if domain else "Aucun")
            st.metric("IPs autorisées", len(current_config['allowed_ips']))
        
        # URLs d'accès
        st.markdown("#### 🔗 URLs d'Accès")
        
        if current_config['ip'] == "127.0.0.1":
            st.info(f"🖥️ **Accès local :** http://127.0.0.1:{current_config['port']}")
        else:
            st.info(f"🖥️ **Accès local :** http://127.0.0.1:{current_config['port']}")
            st.info(f"🌐 **Accès réseau :** http://[IP_DE_VOTRE_MACHINE]:{current_config['port']}")
            
            if current_config.get('custom_domain'):
                st.info(f"🌍 **Domaine personnalisé :** http://{current_config['custom_domain']}:{current_config['port']}")
        
        # Informations sur le mode navigateur
        browser_mode_current = current_config.get('browser_mode', 'headless_always')
        if browser_mode_current == 'headless_always':
            st.success("🔒 **Mode Headless Toujours :** Le navigateur ne s'ouvrira jamais automatiquement")
        elif browser_mode_current == 'headless_network_only':
            st.info("🌐 **Mode Headless Réseau :** Le navigateur s'ouvre seulement pour l'accès local")
        else:
            st.warning("🖥️ **Mode Auto Local :** Le navigateur peut s'ouvrir automatiquement en local")
            
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement de la configuration réseau: {str(e)}")
        st.exception(e)


def show_security_config_in_control_panel(admin_config):
    """Configuration sécurité dans le panneau de contrôle"""
    
    st.subheader("🔒 Gestion de la Sécurité")
    
    # Changement de mot de passe
    with st.form("password_change_form"):
        st.write("**Changer le Mot de Passe Administrateur:**")
        
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
    admin_info = admin_config.config["admin"]
    if admin_info.get("last_login"):
        st.info(f"📅 Dernière connexion admin : {admin_info['last_login']}")


def show_export_config_in_control_panel(admin_config):
    """Export de configuration dans le panneau de contrôle"""
    
    st.subheader("📄 Export de Configuration")
    
    st.info("""
    Générez un résumé technique de la configuration réseau 
    à transmettre à votre équipe IT ou manager réseau.
    """)
    
    if st.button("📋 Générer le Résumé de Configuration"):
        summary_file, summary_content = admin_config.export_config_summary()
        
        st.success(f"✅ Résumé généré : {summary_file}")
        
        # Afficher le contenu
        st.text_area("Configuration pour le Manager Réseau", value=summary_content, height=300)
        
        # Bouton de téléchargement
        st.download_button(
            label="💾 Télécharger le Résumé",
            data=summary_content,
            file_name=summary_file,
            mime="text/plain"
        )


def show_hardware_license_admin_tab(admin_config):
    """Onglet d'administration des licences hardware"""
    
    st.subheader("🔐 Gestion des Licences Hardware")
    
    if not PROTECTION_ENABLED:
        st.warning("""
        ### ⚠️ Protection Hardware Non Activée
        
        Le système de protection hardware n'est pas activé. 
        Pour l'activer, assurez-vous que le module `hardware_protection.py` est présent et redémarrez l'application.
        """)
        return
    
    try:
        license_manager = LicenseManager()
        
        # Vérifier si l'utilisateur a la clé USB (accès administrateur)
        has_usb_access = False
        usb_status = ""
        
        check_usb_method = getattr(license_manager, 'check_usb_token', None)
        if check_usb_method:
            usb_valid, usb_message = check_usb_method()
            if usb_valid:
                has_usb_access = True
                usb_status = usb_message
        
        # Afficher le statut d'accès
        if has_usb_access:
            st.success(f"🔑 **Accès Administrateur Détecté** - {usb_status}")
            st.info("✅ Vous avez accès à toutes les fonctions de gestion des licences")
        else:
            st.warning("⚠️ **Accès Limité** - Clé USB administrateur non détectée")
            st.info("💡 Insérez votre clé USB administrateur pour accéder aux fonctions avancées")
        
        # Statut global des licences
        st.markdown("#### 📊 Vue d'Ensemble")
        
        authorized, message = license_manager.check_license()
        machine_info = license_manager.get_machine_info()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if authorized:
                st.success("✅ Licence Valide")
            else:
                st.error("❌ Licence Invalide")
            
            # Afficher le message de statut
            if message:
                st.caption(f"📝 {message}")
        
        with col2:
            current_mac_count = len(machine_info.get('mac_addresses', []))
            st.metric("MACs Détectées", current_mac_count)
        
        with col3:
            # Compter les autorisations dans license.json
            try:
                hw_protection = license_manager.hw_protection
                hw_protection.load_license()
                authorized_count = len(hw_protection.authorized_macs) + len(hw_protection.authorized_systems)
                st.metric("Autorisations Actives", authorized_count)
            except:
                st.metric("Autorisations Actives", "Erreur")
        
        st.markdown("---")
        
        # Section spéciale pour les utilisateurs avec clé USB
        if has_usb_access:
            st.markdown("#### 🔑 **Gestion Avancée des Adresses MAC** (Accès Administrateur)")
            
            # Onglets pour les différentes fonctions administrateur
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Voir les MACs Autorisées",
                "➕ Ajouter des MACs", 
                "🗑️ Supprimer des MACs",
                "🔧 Outils Avancés"
            ])
            
            with tab1:
                st.markdown("##### 📋 Adresses MAC Actuellement Autorisées")
                
                hw_protection = license_manager.hw_protection
                hw_protection.load_license()
                
                if hw_protection.authorized_macs:
                    # Créer un tableau interactif
                    mac_data = []
                    for i, mac in enumerate(hw_protection.authorized_macs):
                        # Vérifier si cette MAC appartient à la machine actuelle
                        is_current = mac in machine_info.get('mac_addresses', [])
                        mac_data.append({
                            "Index": i + 1,
                            "Adresse MAC": mac,
                            "Statut": "🟢 Machine Actuelle" if is_current else "🔵 Autre Machine"
                        })
                    
                    # Afficher sous forme de tableau
                    for idx, mac_info in enumerate(mac_data):
                        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
                        
                        with col1:
                            st.write(f"**{mac_info['Index']}**")
                        
                        with col2:
                            st.code(mac_info['Adresse MAC'])
                        
                        with col3:
                            st.write(mac_info['Statut'])
                        
                        with col4:
                            if st.button("🗑️", key=f"delete_mac_{idx}", help="Supprimer cette MAC"):
                                if hw_protection.remove_authorization(mac_info['Adresse MAC']):
                                    st.success(f"✅ MAC {mac_info['Adresse MAC']} supprimée")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la suppression")
                else:
                    st.info("Aucune adresse MAC autorisée actuellement.")
            
            with tab2:
                st.markdown("##### ➕ Ajouter de Nouvelles Adresses MAC")
                
                # Sous-onglets pour différentes méthodes d'ajout
                subtab1, subtab2, subtab3 = st.tabs([
                    "🖥️ Machine Actuelle",
                    "✏️ Saisie Manuelle", 
                    "📥 Import en Masse"
                ])
                
                with subtab1:
                    st.markdown("**Autoriser la machine actuelle :**")
                    
                    # Afficher les infos de la machine actuelle
                    st.info(f"""
                    **Machine :** {machine_info.get('hostname', 'Inconnue')}
                    **ID Système :** `{machine_info.get('machine_id', 'Inconnu')}`
                    **Plateforme :** {machine_info.get('platform', 'Inconnue')}
                    """)
                    
                    # Afficher les MACs de cette machine
                    st.markdown("**Adresses MAC de cette machine :**")
                    for mac in machine_info.get('mac_addresses', []):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.code(mac)
                        with col2:
                            if st.button("➕", key=f"add_current_{mac}", help=f"Ajouter {mac}"):
                                hw_protection = license_manager.hw_protection
                                hw_protection.load_license()
                                if mac not in hw_protection.authorized_macs:
                                    hw_protection.authorized_macs.append(mac)
                                    if hw_protection.save_license():
                                        st.success(f"✅ MAC {mac} ajoutée")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur lors de la sauvegarde")
                                else:
                                    st.warning("⚠️ Cette MAC est déjà autorisée")
                    
                    st.markdown("---")
                    if st.button("📝 Autoriser TOUTE Cette Machine", type="primary"):
                        success, reg_message = license_manager.register_machine()
                        if success:
                            st.success(f"✅ {reg_message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {reg_message}")
                
                with subtab2:
                    st.markdown("**Ajouter une adresse MAC manuellement :**")
                    
                    with st.form("add_mac_form"):
                        new_mac = st.text_input(
                            "Adresse MAC", 
                            placeholder="Ex: AA:BB:CC:DD:EE:FF",
                            help="Format attendu : XX:XX:XX:XX:XX:XX"
                        )
                        
                        machine_description = st.text_input(
                            "Description (optionnel)",
                            placeholder="Ex: Ordinateur de bureau - Bureau 1"
                        )
                        
                        submit_mac = st.form_submit_button("➕ Ajouter cette MAC")
                        
                        if submit_mac and new_mac:
                            # Validation du format MAC
                            import re
                            mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
                            
                            if mac_pattern.match(new_mac):
                                # Normaliser le format
                                mac_normalized = new_mac.upper().replace("-", ":")
                                
                                # Ajouter à la liste des autorisées
                                hw_protection = license_manager.hw_protection
                                hw_protection.load_license()
                                if mac_normalized not in hw_protection.authorized_macs:
                                    hw_protection.authorized_macs.append(mac_normalized)
                                    if hw_protection.save_license():
                                        st.success(f"✅ MAC {mac_normalized} ajoutée avec succès")
                                        if machine_description:
                                            st.info(f"📝 Description : {machine_description}")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur lors de la sauvegarde")
                                else:
                                    st.warning("⚠️ Cette adresse MAC est déjà autorisée")
                            else:
                                st.error("❌ Format d'adresse MAC invalide. Utilisez XX:XX:XX:XX:XX:XX")
                
                with subtab3:
                    st.markdown("**Import de plusieurs adresses MAC :**")
                    
                    mac_list_input = st.text_area(
                        "Liste des adresses MAC (une par ligne)",
                        placeholder="""AA:BB:CC:DD:EE:01
AA:BB:CC:DD:EE:02  
AA:BB:CC:DD:EE:03""",
                        height=150
                    )
                    
                    if st.button("📥 Importer les MACs"):
                        if mac_list_input.strip():
                            import re
                            mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
                            
                            lines = [line.strip() for line in mac_list_input.strip().split('\n') if line.strip()]
                            added_macs = []
                            invalid_macs = []
                            duplicate_macs = []
                            
                            hw_protection = license_manager.hw_protection
                            hw_protection.load_license()
                            
                            for line in lines:
                                # Ignorer les commentaires
                                if line.startswith('#'):
                                    continue
                                    
                                # Extraire la MAC (premier mot de la ligne)
                                mac = line.split()[0] if line.split() else ""
                                
                                if mac_pattern.match(mac):
                                    mac_normalized = mac.upper().replace("-", ":")
                                    
                                    if mac_normalized not in hw_protection.authorized_macs:
                                        hw_protection.authorized_macs.append(mac_normalized)
                                        added_macs.append(mac_normalized)
                                    else:
                                        duplicate_macs.append(mac_normalized)
                                else:
                                    invalid_macs.append(line)
                            
                            # Sauvegarder si des MACs ont été ajoutées
                            if added_macs:
                                if hw_protection.save_license():
                                    st.success(f"✅ {len(added_macs)} adresses MAC ajoutées avec succès")
                                    for mac in added_macs:
                                        st.code(mac)
                                else:
                                    st.error("❌ Erreur lors de la sauvegarde")
                            
                            # Afficher les résultats
                            if duplicate_macs:
                                st.warning(f"⚠️ {len(duplicate_macs)} adresses déjà autorisées (ignorées)")
                            
                            if invalid_macs:
                                st.error(f"❌ {len(invalid_macs)} adresses invalides (ignorées)")
                                for invalid in invalid_macs:
                                    st.code(invalid)
                            
                            if added_macs:
                                st.rerun()
            
            with tab3:
                st.markdown("##### 🗑️ Supprimer des Adresses MAC")
                
                hw_protection = license_manager.hw_protection
                hw_protection.load_license()
                
                if hw_protection.authorized_macs:
                    st.markdown("**Sélectionnez les adresses MAC à supprimer :**")
                    
                    # Créer des checkboxes pour chaque MAC
                    macs_to_delete = []
                    for i, mac in enumerate(hw_protection.authorized_macs):
                        is_current = mac in machine_info.get('mac_addresses', [])
                        status_text = "🟢 Machine Actuelle" if is_current else "🔵 Autre Machine"
                        
                        if st.checkbox(f"{mac} ({status_text})", key=f"delete_check_{i}"):
                            macs_to_delete.append(mac)
                    
                    if macs_to_delete:
                        st.markdown("---")
                        st.warning(f"⚠️ **{len(macs_to_delete)} adresse(s) MAC sélectionnée(s) pour suppression**")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🗑️ Confirmer la Suppression", type="secondary"):
                                deleted_count = 0
                                for mac in macs_to_delete:
                                    if hw_protection.remove_authorization(mac):
                                        deleted_count += 1
                                
                                if deleted_count > 0:
                                    st.success(f"✅ {deleted_count} adresse(s) MAC supprimée(s)")
                                    st.rerun()
                        
                        with col2:
                            if st.button("❌ Annuler"):
                                st.rerun()
                else:
                    st.info("Aucune adresse MAC autorisée à supprimer.")
            
            with tab4:
                st.markdown("##### 🔧 Outils Avancés d'Administration")
                
                # Outils de diagnostic et maintenance
                st.markdown("**🔍 Diagnostic et Maintenance :**")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("🔍 Diagnostic Complet", key="admin_diagnostic"):
                        status = license_manager.show_license_status()
                        if isinstance(status, dict):
                            # Nouveau format de statut
                            st.json(status)
                        else:
                            # Ancien format texte
                            st.text_area("Diagnostic", value=status, height=200)
                
                with col2:
                    if st.button("🔄 Recharger Licences", key="admin_reload"):
                        hw_protection.load_license()
                        st.success("✅ Licences rechargées")
                        st.rerun()
                
                with col3:
                    if st.button("💾 Sauvegarder", help="Force la sauvegarde du fichier de licence", key="admin_save"):
                        if hw_protection.save_license():
                            st.success("✅ Licence sauvegardée")
                        else:
                            st.error("❌ Erreur de sauvegarde")
                
                st.markdown("---")
                
                # Gestion de la clé USB
                st.markdown("**🔑 Gestion de la Clé USB :**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔍 Vérifier Clé USB", key="admin_verify_usb"):
                        if check_usb_method:
                            usb_valid, usb_message = check_usb_method()
                            if usb_valid:
                                st.success(f"✅ {usb_message}")
                            else:
                                st.error(f"❌ {usb_message}")
                        else:
                            st.warning("⚠️ Fonction USB non disponible")
                
                with col2:
                    if st.button("🔧 Créer Token USB", key="admin_create_usb"):
                        create_usb_method = getattr(license_manager, 'create_usb_token', None)
                        if create_usb_method:
                            success, message = create_usb_method()
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                        else:
                            st.warning("⚠️ Fonction création USB non disponible")
                
                st.markdown("---")
                
                # Zone de danger (seulement pour les administrateurs avec clé USB)
                st.markdown("**⚠️ Zone de Danger (Administrateur Uniquement) :**")
                
                with st.expander("🚨 Actions Dangereuses"):
                    st.error("""
                    **⚠️ ATTENTION :** Ces actions peuvent affecter l'accès à l'application !
                    Réservé aux administrateurs avec clé USB.
                    """)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🗑️ Supprimer TOUTES les Autorisations", type="secondary", key="danger_delete_all"):
                            if st.button("⚠️ Confirmer la suppression TOTALE", key="confirm_delete_all"):
                                hw_protection.authorized_macs = []
                                hw_protection.authorized_systems = []
                                if hw_protection.save_license():
                                    st.error("❌ Toutes les autorisations ont été supprimées !")
                                    st.rerun()
                    
                    with col2:
                        if st.button("🔄 Réinitialiser les Licences", key="danger_reset_licenses"):
                            # Supprimer le fichier de licence pour forcer la réinitialisation
                            try:
                                import os
                                if os.path.exists("license.json"):
                                    os.remove("license.json")
                                st.warning("⚠️ Fichier de licence supprimé. Redémarrez l'application.")
                            except Exception as e:
                                st.error(f"❌ Erreur : {e}")
        
        else:
            # Interface limitée pour les utilisateurs sans clé USB
            st.markdown("#### 🔒 Gestion Limitée des Licences")
            
            # Gestion des adresses MAC autorisées (lecture seule)
            st.markdown("##### 📋 Adresses MAC Autorisées (Lecture Seule)")
            
            hw_protection = license_manager.hw_protection
            hw_protection.load_license()
            
            if hw_protection.authorized_macs:
                st.write("**Adresses MAC actuellement autorisées :**")
                
                for i, mac in enumerate(hw_protection.authorized_macs):
                    # Vérifier si cette MAC appartient à la machine actuelle
                    is_current = mac in machine_info.get('mac_addresses', [])
                    col1, col2, col3 = st.columns([1, 3, 2])
                    
                    with col1:
                        st.write(f"**{i + 1}**")
                    
                    with col2:
                        st.code(mac)
                    
                    with col3:
                        if is_current:
                            st.success("🟢 Machine Actuelle")
                        else:
                            st.info("🔵 Autre Machine")
            else:
                st.info("Aucune adresse MAC autorisée actuellement.")
            
            st.markdown("---")
            
            # Actions limitées
            st.markdown("##### ⚙️ Actions Disponibles")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📝 Enregistrer cette Machine", type="primary", key="limited_register_machine"):
                    success, reg_message = license_manager.register_machine()
                    if success:
                        st.success(f"✅ {reg_message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {reg_message}")
            
            with col2:
                if st.button("🔄 Vérifier la Licence", key="limited_verify_license"):
                    st.rerun()
            
            # Message d'information pour obtenir plus d'accès
            st.markdown("---")
            st.info("""
            💡 **Pour accéder aux fonctions avancées de gestion des adresses MAC :**
            
            1. Insérez votre clé USB administrateur
            2. Assurez-vous que le fichier `sys.dat` est présent sur la clé
            3. Rechargez cette page
            
            **Fonctions avancées disponibles avec la clé USB :**
            - ➕ Ajouter des adresses MAC manuellement
            - 🗑️ Supprimer des adresses MAC
            - 📥 Import en masse d'adresses MAC
            - 🔧 Outils de diagnostic avancés
            - 🔑 Gestion de la clé USB
            """)
        
        # Informations de la machine avec menu de gestion des MACs
        st.markdown("---")
        st.markdown("#### 🖥️ Informations de la Machine Actuelle")
        
        # Utiliser la nouvelle fonction avec menu interactif
        show_machine_info_with_mac_management(license_manager, has_usb_access)
        
        # Aide (toujours visible)
        st.markdown("---")
        st.markdown("#### 💡 Aide")
        
        with st.expander("Comment fonctionne la protection ?"):
            st.markdown("""
            ### 🛡️ Système de Protection Hardware
            
            **Principe :**
            - Le logiciel génère un ID unique basé sur votre hardware (adresse MAC, etc.)
            - Seules les machines autorisées peuvent utiliser le logiciel
            - La licence est stockée localement dans un fichier `license.json`
            - **Clé USB** : Accès administrateur pour gérer les autorisations
            
            **Utilisation :**
            1. **Première utilisation :** Cliquez sur "Enregistrer cette Machine"
            2. **Déploiement :** Copiez le fichier `license.json` sur les autres machines autorisées
            3. **Administration :** Utilisez la clé USB pour gérer les autorisations
            4. **Vérification :** Le système vérifie automatiquement à chaque démarrage
            
            **Sécurité :**
            - Basé sur l'adresse MAC (identifiant hardware unique)
            - ID système généré avec hachage SHA-256
            - Protection contre la copie non autorisée
            - **Clé USB** : Contrôle d'accès administrateur
            """)
        
        with st.expander("Dépannage"):
            st.markdown("""
            ### 🔧 Résolution des Problèmes
            
            **"Machine non autorisée" :**
            - Vérifiez que le fichier `license.json` existe
            - Cliquez sur "Enregistrer cette Machine"
            - Contactez l'administrateur avec votre ID système
            
            **"Fichier de licence corrompu" :**
            - Supprimez le fichier `license.json`
            - Ré-enregistrez la machine
            
            **Changement de carte réseau :**
            - L'adresse MAC a changé
            - Ré-enregistrez la machine ou copiez la licence d'une machine autorisée
            
            **Accès administrateur :**
            - Insérez la clé USB avec le fichier `sys.dat`
            - Vérifiez que la clé est sur le lecteur G:
            - Rechargez la page
            """)
            
    except Exception as e:
        st.error(f"❌ Erreur lors de l'accès au système de licence : {str(e)}")
        
        if st.button("🔧 Diagnostics Détaillés"):
            st.code(f"""
Erreur détaillée : {str(e)}
Type d'erreur : {type(e).__name__}
Module protection disponible : {PROTECTION_ENABLED}
            """)


def show_license_tab():
    """Onglet de gestion des licences"""
    
    st.header("🔐 Gestion des Licences")
    
    if not PROTECTION_ENABLED:
        st.info("""
        ### ℹ️ Protection Hardware Non Activée
        
        Le système de protection hardware n'est pas activé sur cette installation.
        Pour activer la protection basée sur l'adresse MAC :
        
        1. Assurez-vous que le module `hardware_protection.py` est présent
        2. Redémarrez l'application
        """)
        return
    
    try:
        license_manager = LicenseManager()
        
        # Statut actuel
        st.subheader("📋 Statut de la Licence")
        
        authorized, message = license_manager.check_license()
        machine_info = license_manager.get_machine_info()
        
        if authorized:
            st.success(f"✅ **Licence Valide** - {message}")
        else:
            st.error(f"❌ **Licence Invalide** - {message}")
        
        # Informations de la machine avec menu de gestion des MACs
        st.markdown("---")
        st.subheader("🖥️ Informations de la Machine")
        
        # Vérifier si l'utilisateur a la clé USB pour les permissions avancées
        has_usb_access = False
        check_usb_method = getattr(license_manager, 'check_usb_token', None)
        if check_usb_method:
            usb_valid, _ = check_usb_method()
            has_usb_access = usb_valid
        
        # Utiliser la nouvelle fonction avec menu interactif
        show_machine_info_with_mac_management(license_manager, has_usb_access)
        
        # Actions
        st.markdown("---")
        st.subheader("⚙️ Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Enregistrer cette Machine", type="primary", key="license_register_machine"):
                success, reg_message = license_manager.register_machine()
                if success:
                    st.success(f"✅ {reg_message}")
                    st.rerun()
                else:
                    st.error(f"❌ {reg_message}")
        
        with col2:
            if st.button("🔄 Vérifier la Licence", key="license_verify"):
                st.rerun()
        
        with col3:
            if st.button("📊 Statut Détaillé", key="license_status"):
                status = license_manager.show_license_status()
                st.text_area("Statut Complet", value=status, height=300)
        
        # Aide
        st.markdown("---")
        st.subheader("💡 Aide")
        
        with st.expander("Comment fonctionne la protection ?"):
            st.markdown("""
            ### 🛡️ Système de Protection Hardware
            
            **Principe :**
            - Le logiciel génère un ID unique basé sur votre hardware (adresse MAC, etc.)
            - Seules les machines autorisées peuvent utiliser le logiciel
            - La licence est stockée localement dans un fichier `license.json`
            - **Clé USB** : Accès administrateur pour gérer les autorisations
            
            **Utilisation :**
            1. **Première utilisation :** Cliquez sur "Enregistrer cette Machine"
            2. **Déploiement :** Copiez le fichier `license.json` sur les autres machines autorisées
            3. **Administration :** Utilisez la clé USB pour gérer les autorisations
            4. **Vérification :** Le système vérifie automatiquement à chaque démarrage
            
            **Sécurité :**
            - Basé sur l'adresse MAC (identifiant hardware unique)
            - ID système généré avec hachage SHA-256
            - Protection contre la copie non autorisée
            - **Clé USB** : Contrôle d'accès administrateur
            """)
        
        with st.expander("Dépannage"):
            st.markdown("""
            ### 🔧 Résolution des Problèmes
            
            **"Machine non autorisée" :**
            - Vérifiez que le fichier `license.json` existe
            - Cliquez sur "Enregistrer cette Machine"
            - Contactez l'administrateur avec votre ID système
            
            **"Fichier de licence corrompu" :**
            - Supprimez le fichier `license.json`
            - Ré-enregistrez la machine
            
            **Changement de carte réseau :**
            - L'adresse MAC a changé
            - Ré-enregistrez la machine ou copiez la licence d'une machine autorisée
            
            **Accès administrateur :**
            - Insérez la clé USB avec le fichier `sys.dat`
            - Vérifiez que la clé est sur le lecteur G:
            - Rechargez la page
            """)
            
    except Exception as e:
        st.error(f"❌ Erreur lors de l'accès au système de licence : {str(e)}")
        
        if st.button("🔧 Diagnostics"):
            st.code(f"""
Erreur détaillée : {str(e)}
Type d'erreur : {type(e).__name__}
Module protection disponible : {PROTECTION_ENABLED}
            """)


def show_machine_info_with_mac_management(license_manager, has_usb_access=False):
    """Affiche les informations de la machine avec menu de gestion des MACs"""
    
    try:
        machine_info = license_manager.get_machine_info()
        hw_protection = license_manager.hw_protection
        hw_protection.load_license()
        
        # Informations de base de la machine
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.info(f"""
            **Nom de la machine:** {machine_info.get('hostname', 'Inconnu')}
            **ID Système:** `{machine_info.get('machine_id', 'Inconnu')}`
            **Plateforme:** {machine_info.get('platform', 'Inconnue')}
            """)
        
        with col2:
            # Statistiques des MACs
            total_macs = len(machine_info.get('mac_addresses', []))
            authorized_macs = len([mac for mac in machine_info.get('mac_addresses', []) 
                                 if mac in hw_protection.authorized_macs])
            
            st.metric("MACs Détectées", total_macs)
            st.metric("MACs Autorisées", f"{authorized_macs}/{total_macs}")
        
        # Section des adresses MAC avec menu de gestion
        st.markdown("#### 🌐 Adresses MAC Détectées")
        
        mac_addresses = machine_info.get('mac_addresses', [])
        
        if not mac_addresses:
            st.warning("Aucune adresse MAC détectée sur cette machine")
            return
        
        # Affichage interactif des MACs
        for i, mac in enumerate(mac_addresses):
            # Vérifier si cette MAC est autorisée
            is_authorized = mac in hw_protection.authorized_macs
            
            # Conteneur pour chaque MAC
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    # Affichage de la MAC avec statut
                    if is_authorized:
                        st.success(f"🟢 `{mac}`")
                    else:
                        st.error(f"🔴 `{mac}`")
                
                with col2:
                    # Statut textuel
                    if is_authorized:
                        st.write("✅ **Autorisée**")
                    else:
                        st.write("❌ **Non autorisée**")
                
                with col3:
                    # Actions selon les permissions
                    if has_usb_access:
                        # Administrateur avec clé USB
                        if is_authorized:
                            if st.button("🗑️ Supprimer", key=f"remove_mac_{i}", 
                                       help=f"Supprimer l'autorisation pour {mac}"):
                                if hw_protection.remove_authorization(mac):
                                    st.success(f"✅ MAC {mac} supprimée des autorisations")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la suppression")
                        else:
                            if st.button("➕ Autoriser", key=f"add_mac_{i}", 
                                       help=f"Autoriser {mac}"):
                                if mac not in hw_protection.authorized_macs:
                                    hw_protection.authorized_macs.append(mac)
                                    if hw_protection.save_license():
                                        st.success(f"✅ MAC {mac} autorisée")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur lors de la sauvegarde")
                                else:
                                    st.warning("⚠️ MAC déjà autorisée")
                    else:
                        # Utilisateur standard
                        if is_authorized:
                            st.write("🔒 *Autorisée*")
                        else:
                            st.write("🔒 *Non autorisée*")
                
                with col4:
                    # Informations supplémentaires
                    if st.button("ℹ️", key=f"info_mac_{i}", help=f"Informations sur {mac}"):
                        # Afficher des informations détaillées sur cette MAC
                        st.info(f"""
                        **Adresse MAC:** `{mac}`
                        **Format normalisé:** `{mac.upper().replace('-', ':')}`
                        **Statut:** {'Autorisée' if is_authorized else 'Non autorisée'}
                        **Type:** Interface réseau #{i+1}
                        """)
                
                # Ligne de séparation
                if i < len(mac_addresses) - 1:
                    st.markdown("---")
        
        # Actions globales
        st.markdown("---")
        st.markdown("#### ⚙️ Actions Globales")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if has_usb_access:
                # Autoriser toutes les MACs de cette machine
                unauthorized_macs = [mac for mac in mac_addresses 
                                   if mac not in hw_protection.authorized_macs]
                
                if unauthorized_macs:
                    if st.button("✅ Autoriser TOUTES les MACs", type="primary"):
                        added_count = 0
                        for mac in unauthorized_macs:
                            if mac not in hw_protection.authorized_macs:
                                hw_protection.authorized_macs.append(mac)
                                added_count += 1
                        
                        if hw_protection.save_license():
                            st.success(f"✅ {added_count} adresse(s) MAC autorisée(s)")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.success("✅ Toutes les MACs sont déjà autorisées")
            else:
                # Enregistrer cette machine (fonction standard)
                if st.button("📝 Enregistrer cette Machine", type="primary", key="machine_info_register"):
                    success, reg_message = license_manager.register_machine()
                    if success:
                        st.success(f"✅ {reg_message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {reg_message}")
        
        with col2:
            if has_usb_access:
                # Supprimer toutes les MACs de cette machine
                authorized_macs_here = [mac for mac in mac_addresses 
                                      if mac in hw_protection.authorized_macs]
                
                if authorized_macs_here:
                    if st.button("🗑️ Supprimer TOUTES les MACs", type="secondary"):
                        if st.button("⚠️ Confirmer la suppression", key="confirm_remove_all_macs"):
                            removed_count = 0
                            for mac in authorized_macs_here:
                                if hw_protection.remove_authorization(mac):
                                    removed_count += 1
                            
                            if removed_count > 0:
                                st.success(f"✅ {removed_count} adresse(s) MAC supprimée(s)")
                                st.rerun()
                else:
                    st.info("ℹ️ Aucune MAC autorisée à supprimer")
            else:
                # Vérifier la licence
                if st.button("🔄 Vérifier la Licence", key="machine_info_verify"):
                    st.rerun()
        
        with col3:
            # Diagnostic des MACs
            if st.button("🔍 Diagnostic MACs", key="machine_info_diagnostic"):
                st.markdown("##### 📊 Diagnostic des Adresses MAC")
                
                # Statistiques détaillées
                total = len(mac_addresses)
                authorized = len([mac for mac in mac_addresses if mac in hw_protection.authorized_macs])
                unauthorized = total - authorized
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total", total)
                with col_b:
                    st.metric("Autorisées", authorized, delta=f"{authorized/total*100:.0f}%" if total > 0 else "0%")
                with col_c:
                    st.metric("Non autorisées", unauthorized, delta=f"{unauthorized/total*100:.0f}%" if total > 0 else "0%")
                
                # Détails par MAC
                st.markdown("**Détails par adresse MAC :**")
                for mac in mac_addresses:
                    status = "✅ Autorisée" if mac in hw_protection.authorized_macs else "❌ Non autorisée"
                    st.write(f"- `{mac}` : {status}")
        
        # Section de gestion avancée des MACs (avec clé USB)
        if has_usb_access:
            st.markdown("---")
            st.markdown("#### 🔧 Gestion Avancée des Adresses MAC")
            
            # Onglets pour organiser les fonctionnalités
            tab_add, tab_list, tab_import = st.tabs(["➕ Ajouter MAC", "📋 Liste Complète", "📥 Import/Export"])
            
            with tab_add:
                st.markdown("##### ➕ Ajouter une Adresse MAC Manuellement")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Champ de saisie pour nouvelle MAC
                    new_mac = st.text_input(
                        "Adresse MAC à ajouter",
                        placeholder="Ex: 04:D4:C4:55:AD:45 ou 04-D4-C4-55-AD-45",
                        help="Entrez une adresse MAC au format XX:XX:XX:XX:XX:XX ou XX-XX-XX-XX-XX-XX"
                    )
                    
                    # Description optionnelle
                    mac_description = st.text_input(
                        "Description (optionnel)",
                        placeholder="Ex: PC Bureau - Salle 1",
                        help="Description pour identifier cette machine"
                    )
                
                with col2:
                    st.markdown("**Formats acceptés:**")
                    st.code("""
04:D4:C4:55:AD:45
04-D4-C4-55-AD-45
04d4c455ad45
                    """)
                
                # Bouton d'ajout
                if st.button("➕ Ajouter cette MAC", type="primary", key="add_manual_mac"):
                    if new_mac.strip():
                        # Normaliser le format de la MAC
                        normalized_mac = normalize_mac_address(new_mac.strip())
                        
                        if normalized_mac:
                            if normalized_mac not in hw_protection.authorized_macs:
                                # Ajouter la MAC avec description
                                hw_protection.authorized_macs.append(normalized_mac)
                                
                                # Sauvegarder avec description si fournie
                                if mac_description.strip():
                                    # Ajouter la description dans les métadonnées
                                    if not hasattr(hw_protection, 'mac_descriptions'):
                                        hw_protection.mac_descriptions = {}
                                    hw_protection.mac_descriptions[normalized_mac] = mac_description.strip()
                                
                                if hw_protection.save_license():
                                    st.success(f"✅ MAC {normalized_mac} ajoutée avec succès!")
                                    if mac_description.strip():
                                        st.info(f"📝 Description: {mac_description.strip()}")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la sauvegarde")
                            else:
                                st.warning(f"⚠️ MAC {normalized_mac} déjà autorisée")
                        else:
                            st.error("❌ Format d'adresse MAC invalide")
                    else:
                        st.error("❌ Veuillez entrer une adresse MAC")
            
            with tab_list:
                st.markdown("##### 📋 Toutes les Adresses MAC Autorisées")
                
                all_authorized_macs = hw_protection.authorized_macs
                
                if all_authorized_macs:
                    st.info(f"**Total: {len(all_authorized_macs)} adresse(s) MAC autorisée(s)**")
                    
                    # Filtrage et recherche
                    search_mac = st.text_input("🔍 Rechercher une MAC", placeholder="Tapez pour filtrer...")
                    
                    # Filtrer les MACs selon la recherche
                    if search_mac:
                        filtered_macs = [mac for mac in all_authorized_macs 
                                       if search_mac.lower() in mac.lower()]
                    else:
                        filtered_macs = all_authorized_macs
                    
                    # Affichage de toutes les MACs autorisées
                    for i, mac in enumerate(filtered_macs):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                # Vérifier si c'est une MAC de cette machine
                                is_local = mac in mac_addresses
                                if is_local:
                                    st.success(f"🏠 `{mac}` *(Cette machine)*")
                                else:
                                    st.info(f"🌐 `{mac}` *(Machine externe)*")
                            
                            with col2:
                                # Description si disponible
                                description = getattr(hw_protection, 'mac_descriptions', {}).get(mac, "")
                                if description:
                                    st.write(f"📝 {description}")
                                else:
                                    st.write("*Pas de description*")
                            
                            with col3:
                                # Statut et actions
                                if is_local:
                                    st.write("✅ **Machine locale**")
                                else:
                                    st.write("🌐 **Machine externe**")
                            
                            with col4:
                                # Bouton de suppression
                                if st.button("🗑️", key=f"remove_all_mac_{i}", 
                                           help=f"Supprimer {mac}"):
                                    if hw_protection.remove_authorization(mac):
                                        # Supprimer aussi la description
                                        if hasattr(hw_protection, 'mac_descriptions') and mac in hw_protection.mac_descriptions:
                                            del hw_protection.mac_descriptions[mac]
                                            hw_protection.save_license()
                                        st.success(f"✅ MAC {mac} supprimée")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur lors de la suppression")
                            
                            # Ligne de séparation
                            if i < len(filtered_macs) - 1:
                                st.markdown("---")
                    
                    # Actions globales sur toutes les MACs
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🗑️ Supprimer TOUTES les MACs", type="secondary"):
                            if st.button("⚠️ CONFIRMER - Supprimer toutes les autorisations", 
                                       key="confirm_remove_all_authorized"):
                                hw_protection.authorized_macs.clear()
                                if hasattr(hw_protection, 'mac_descriptions'):
                                    hw_protection.mac_descriptions.clear()
                                if hw_protection.save_license():
                                    st.success("✅ Toutes les autorisations supprimées")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la sauvegarde")
                    
                    with col2:
                        # Exporter la liste
                        mac_list_text = "\n".join([
                            f"{mac} - {getattr(hw_protection, 'mac_descriptions', {}).get(mac, 'Pas de description')}"
                            for mac in all_authorized_macs
                        ])
                        st.download_button(
                            "📥 Exporter la liste",
                            data=mac_list_text,
                            file_name="macs_autorisees.txt",
                            mime="text/plain"
                        )
                else:
                    st.warning("Aucune adresse MAC autorisée")
            
            with tab_import:
                st.markdown("##### 📥 Import/Export en Lot")
                
                # Import de MACs en lot
                st.markdown("**📥 Importer des MACs en lot:**")
                
                bulk_macs = st.text_area(
                    "Adresses MAC (une par ligne)",
                    placeholder="""04:D4:C4:55:AD:45
AA:BB:CC:DD:EE:FF
12-34-56-78-90-AB""",
                    height=100,
                    help="Entrez une adresse MAC par ligne, avec ou sans description"
                )
                
                if st.button("📥 Importer ces MACs", type="primary"):
                    if bulk_macs.strip():
                        lines = bulk_macs.strip().split('\n')
                        added_count = 0
                        errors = []
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Séparer MAC et description éventuelle
                            parts = line.split(' - ', 1)
                            mac_part = parts[0].strip()
                            description_part = parts[1].strip() if len(parts) > 1 else ""
                            
                            # Normaliser la MAC
                            normalized_mac = normalize_mac_address(mac_part)
                            
                            if normalized_mac:
                                if normalized_mac not in hw_protection.authorized_macs:
                                    hw_protection.authorized_macs.append(normalized_mac)
                                    
                                    # Ajouter description si fournie
                                    if description_part:
                                        if not hasattr(hw_protection, 'mac_descriptions'):
                                            hw_protection.mac_descriptions = {}
                                        hw_protection.mac_descriptions[normalized_mac] = description_part
                                    
                                    added_count += 1
                            else:
                                errors.append(f"Format invalide: {mac_part}")
                        
                        # Sauvegarder
                        if added_count > 0:
                            if hw_protection.save_license():
                                st.success(f"✅ {added_count} adresse(s) MAC importée(s)")
                                if errors:
                                    st.warning(f"⚠️ {len(errors)} erreur(s): " + ", ".join(errors))
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la sauvegarde")
                        else:
                            st.error("❌ Aucune MAC valide à importer")
                            if errors:
                                for error in errors:
                                    st.error(error)
                    else:
                        st.error("❌ Veuillez entrer des adresses MAC")
                
                # Export formaté
                st.markdown("---")
                st.markdown("**📤 Exporter la configuration:**")
                
                if all_authorized_macs:
                    # Format détaillé avec descriptions
                    export_data = {
                        "authorized_macs": all_authorized_macs,
                        "descriptions": getattr(hw_protection, 'mac_descriptions', {}),
                        "export_date": datetime.now().isoformat(),
                        "total_count": len(all_authorized_macs)
                    }
                    
                    import json
                    export_json = json.dumps(export_data, indent=2, ensure_ascii=False)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            "📤 Exporter en JSON",
                            data=export_json,
                            file_name=f"optimpv_macs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    with col2:
                        # Format texte simple
                        simple_text = "\n".join(all_authorized_macs)
                        st.download_button(
                            "📤 Exporter en TXT",
                            data=simple_text,
                            file_name=f"optimpv_macs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )

        # Message d'aide selon les permissions
        if has_usb_access:
            st.info("""
            💡 **Avec votre clé USB administrateur, vous pouvez :**
            - ➕ Autoriser/supprimer individuellement chaque adresse MAC
            - ✅ Autoriser toutes les MACs de cette machine d'un coup
            - 🗑️ Supprimer toutes les autorisations de cette machine
            - 🔧 Ajouter manuellement des MACs d'autres machines
            - 📋 Gérer toutes les MACs autorisées (locales et externes)
            - 📥 Importer/exporter des listes de MACs en lot
            - 🔍 Diagnostiquer l'état des autorisations
            """)
        else:
            st.info("""
            💡 **Actions disponibles :**
            - 📝 Enregistrer cette machine pour l'autoriser
            - 🔄 Vérifier le statut de la licence
            - 🔍 Voir le diagnostic des adresses MAC
            
            **Pour plus d'options :** Insérez votre clé USB administrateur
            """)
            
    except Exception as e:
        st.error(f"❌ Erreur lors de l'affichage des informations machine : {str(e)}")


if __name__ == "__main__":
    main_control_panel() 