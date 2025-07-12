#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV Control Panel - Version avec débogage amélioré
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import subprocess
import webbrowser
from pathlib import Path
import logging
import multiprocessing
import socket
import psutil
from datetime import datetime

# Import du module de protection
try:
    from licence_guard import LicenceGuard, initialize_protection
except ImportError:
    print("ERREUR: Module licence_guard.py introuvable!")
    sys.exit(1)

# Configuration du logging avec gestion PyInstaller
def setup_logging():
    """Configuration du logging adaptée à PyInstaller"""
    # Déterminer le répertoire de base
    if getattr(sys, 'frozen', False):
        # En mode PyInstaller
        base_dir = os.path.dirname(sys.executable)
    else:
        # En mode développement
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_file = os.path.join(base_dir, 'optimpv_controller.log')
    
    # Créer le fichier de log s'il n'existe pas
    try:
        with open(log_file, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Session démarrée: {datetime.now()}\n")
            f.write(f"{'='*60}\n")
    except:
        pass
    
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return log_file

# Initialiser le logging
LOG_FILE_PATH = setup_logging()

class OptimPVController:
    def __init__(self):
        # Vérification de la licence AVANT toute chose
        self.verify_licence()
        
        # Initialisation de l'interface
        self.root = tk.Tk()
        self.root.title("OptimPV Control Panel")
        self.root.geometry("450x350")  # Plus grande pour afficher le debug
        self.root.resizable(False, False)
        
        # Variables d'état - IMPORTANT: initialiser AVANT la création de l'UI
        self.streamlit_thread = None
        self.streamlit_process = None  # Pour subprocess
        self.server_running = False  # État initial TOUJOURS False
        self.status_var = tk.StringVar(value="Serveur arrêté")
        self.debug_var = tk.StringVar(value="Debug: Initialisation...")
        
        logging.info("Initialisation du contrôleur OptimPV")
        logging.info(f"État initial du serveur: {self.server_running}")
        logging.info(f"Fichier de log: {LOG_FILE_PATH}")
        
        # Configuration des styles modernes
        self.setup_modern_styles()
        
        # Création de l'interface
        self.create_modern_ui()
        
        # FORCER l'état initial des boutons après un court délai
        self.root.after(100, self.force_initial_state)
        
        # CRUCIAL: Vérifier l'état existant APRÈS création de l'UI
        self.root.after(500, self.check_server_status)
        
        # Fermeture propre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Centrer la fenêtre
        self.center_window()
        
        logging.info("Initialisation du contrôleur terminée")
        self.update_debug("Initialisation terminée")
        
    def update_debug(self, message):
        """Mettre à jour le message de debug"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_var.set(f"[{timestamp}] {message}")
        self.root.update_idletasks()
        
    def force_initial_state(self):
        """Forcer l'état initial des boutons"""
        logging.info("Force de l'état initial des boutons...")
        self.update_debug("Initialisation des boutons...")
        
        try:
            # Forcer l'état des boutons directement
            self.start_button.config(state='normal')
            self.stop_button.config(state='disabled')
            
            # Mettre à jour l'indicateur
            self.update_status_indicator(False)
            
            logging.info("État initial forcé: START activé, STOP désactivé")
            self.update_debug("Boutons initialisés: START activé")
            
        except Exception as e:
            logging.error(f"Erreur lors du forçage de l'état initial: {e}")
            self.update_debug(f"Erreur init: {e}")
        
    def verify_licence(self):
        """Vérification de la licence au démarrage"""
        logging.info("Vérification de la licence OptimPV...")
        
        # Initialiser la protection
        if not initialize_protection():
            messagebox.showerror(
                "Erreur de Licence",
                "Licence OptimPV invalide ou introuvable.\n\n"
                "Veuillez contacter votre administrateur."
            )
            sys.exit(1)
        
        logging.info("Licence validée avec succès")
        
    def setup_modern_styles(self):
        """Configuration des styles modernes"""
        # Couleurs Streamlit
        self.colors = {
            'primary': '#1f77b4',
            'primary_dark': '#0e5a8a',
            'bg_main': '#ffffff',
            'text_primary': '#262730',
            'success': '#21c354',
            'error': '#ff4b4b',
        }
        
        self.root.configure(bg=self.colors['bg_main'])
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel',
                       background=self.colors['bg_main'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 24, 'bold'))
        
        style.configure('Status.TLabel',
                       background=self.colors['bg_main'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 12))
        
        style.configure('Debug.TLabel',
                       background=self.colors['bg_main'],
                       foreground='#666666',
                       font=('Consolas', 9))
        
        style.configure('Modern.TFrame',
                       background=self.colors['bg_main'],
                       relief='flat')
        
        style.configure('Start.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       foreground='white',
                       background=self.colors['primary'],
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        
        style.map('Start.TButton',
                 background=[('active', self.colors['primary_dark']),
                           ('pressed', self.colors['primary_dark']),
                           ('disabled', '#cccccc')])
        
        style.configure('Stop.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       foreground='white',
                       background=self.colors['error'],
                       borderwidth=0,
                       focuscolor='none',
                       relief='flat')
        
        style.map('Stop.TButton',
                 background=[('active', '#e63946'),
                           ('pressed', '#d62828'),
                           ('disabled', '#cccccc')])
        
    def create_modern_ui(self):
        """Création de l'interface moderne avec debug"""
        main_frame = ttk.Frame(self.root, style='Modern.TFrame', padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        title_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        title_frame.grid(row=0, column=0, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, 
                               text="OptimPV", 
                               style='Title.TLabel')
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame,
                                  text="Optimisation Autoconsommation Photovoltaïque",
                                  font=('Segoe UI', 10),
                                  foreground=self.colors['text_primary'],
                                  background=self.colors['bg_main'])
        subtitle_label.pack()
        
        # Statut
        status_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        status_frame.grid(row=1, column=0, pady=(0, 20))
        
        self.status_canvas = tk.Canvas(status_frame, 
                                      width=200, height=40,
                                      bg=self.colors['bg_main'],
                                      highlightthickness=0)
        self.status_canvas.pack()
        
        self.status_label = ttk.Label(status_frame, 
                                     textvariable=self.status_var,
                                     style='Status.TLabel')
        self.status_label.pack()
        
        # Boutons
        button_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        button_frame.grid(row=2, column=0, pady=(0, 15))
        
        self.start_button = ttk.Button(button_frame, 
                                      text="START Serveur",
                                      command=self.start_server,
                                      style='Start.TButton',
                                      width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, 
                                     text="STOP Serveur",
                                     command=self.stop_server,
                                     style='Stop.TButton',
                                     width=20)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Zone de debug
        debug_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        debug_frame.grid(row=3, column=0, pady=(10, 0))
        
        self.debug_label = ttk.Label(debug_frame,
                                    textvariable=self.debug_var,
                                    style='Debug.TLabel')
        self.debug_label.pack()
        
        # Footer
        footer_label = ttk.Label(main_frame,
                                text="2025 OptimPV Pro - Licence activée",
                                font=('Segoe UI', 8),
                                foreground=self.colors['text_primary'],
                                background=self.colors['bg_main'])
        footer_label.grid(row=4, column=0, pady=(15, 0))
        
        # ÉTAT INITIAL - ne pas appeler update_ui_state ici
        # car les styles ttk peuvent ne pas être complètement initialisés
        logging.info("Interface créée, état initial en attente...")
        
    def check_server_status(self):
        """Vérifier si un serveur Streamlit est déjà en cours au démarrage"""
        logging.info("Vérification de l'état du serveur existant...")
        self.update_debug("Vérification serveur existant...")
        
        try:
            # Vérifier si le port 8501 est occupé
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8501))
            sock.close()
            
            if result == 0:
                logging.info("Port 8501 occupé - vérification des processus Streamlit...")
                self.update_debug("Port 8501 occupé")
                
                # Chercher des processus Streamlit
                streamlit_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and any('streamlit' in str(arg).lower() for arg in cmdline):
                            if any('8501' in str(arg) for arg in cmdline):
                                streamlit_processes.append(proc)
                                logging.info(f"Processus Streamlit trouvé: PID {proc.info['pid']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if streamlit_processes:
                    logging.info(f"Serveur Streamlit existant détecté ({len(streamlit_processes)} processus)")
                    self.update_debug("Serveur existant détecté")
                    self.update_ui_state(True)
                    return
                else:
                    logging.info("Port occupé mais aucun processus Streamlit trouvé")
                    self.update_debug("Port occupé, pas de Streamlit")
            else:
                logging.info("Port 8501 libre - aucun serveur existant")
                self.update_debug("Port 8501 libre")
                
        except Exception as e:
            logging.warning(f"Erreur lors de la vérification du serveur existant: {e}")
            self.update_debug(f"Erreur vérif: {e}")
        
        # État par défaut: serveur arrêté
        logging.info("Aucun serveur existant trouvé - état initial: arrêté")
        self.update_ui_state(False)
        
    def update_status_indicator(self, running):
        """Indicateur d'état moderne"""
        self.status_canvas.delete("all")
        
        if running:
            color = self.colors['success']
            text = "EN LIGNE"
            self.status_var.set("Serveur en cours d'exécution")
        else:
            color = self.colors['error']
            text = "ARRÊTÉ"
            self.status_var.set("Serveur arrêté")
        
        self.status_canvas.create_rectangle(0, 10, 200, 30,
                                          fill=color,
                                          outline="",
                                          width=0)
        
        self.status_canvas.create_text(100, 20,
                                     text=text,
                                     fill="white",
                                     font=('Segoe UI', 10, 'bold'))
    
    def update_ui_state(self, running):
        """Mettre à jour l'état de l'interface"""
        logging.info(f"Mise à jour de l'état de l'interface: running={running}")
        self.update_debug(f"État UI: {'Running' if running else 'Stopped'}")
        
        # Mettre à jour l'état interne
        self.server_running = running
        
        # Mettre à jour l'indicateur visuel
        self.update_status_indicator(running)
        
        # Mise à jour des boutons avec vérification
        try:
            if running:
                # Serveur en cours: désactiver START, activer STOP
                self.start_button.config(state='disabled')
                self.stop_button.config(state='normal')
                logging.info("Boutons mis à jour: START désactivé, STOP activé")
                self.update_debug("Boutons: START off, STOP on")
            else:
                # Serveur arrêté: activer START, désactiver STOP
                self.start_button.config(state='normal')
                self.stop_button.config(state='disabled')
                logging.info("Boutons mis à jour: START activé, STOP désactivé")
                self.update_debug("Boutons: START on, STOP off")
        except Exception as e:
            logging.error(f"Erreur lors de la mise à jour des boutons: {e}")
            self.update_debug(f"Erreur boutons: {e}")
    
    def start_server(self):
        """Démarrer le serveur Streamlit dans un thread"""
        if self.server_running:
            logging.warning("Tentative de démarrage alors que le serveur est déjà en cours")
            self.update_debug("Serveur déjà actif!")
            return
            
        logging.info("=== DÉBUT DÉMARRAGE DU SERVEUR ===")
        self.update_debug("Démarrage serveur...")
        self.start_button.config(state='disabled')
        
        # Lancer Streamlit dans un thread séparé
        self.streamlit_thread = threading.Thread(target=self._run_streamlit, daemon=True)
        self.streamlit_thread.start()
        
        # Attendre un peu puis vérifier si le serveur répond
        threading.Thread(target=self._check_server_startup, daemon=True).start()
    
    def _run_streamlit(self):
        """Lance Streamlit dans le thread actuel"""
        try:
            logging.info("Démarrage du thread Streamlit...")
            self.update_debug("Thread Streamlit lancé")
            
            # Import retardé pour éviter les conflits
            logging.info("Import de Streamlit...")
            
            try:
                import streamlit.web.cli as stcli
                logging.info("Streamlit importé avec succès")
                self.update_debug("Streamlit importé OK")
            except ImportError as e:
                logging.error(f"Impossible d'importer Streamlit: {e}")
                self.update_debug("Erreur import Streamlit!")
                return
            
            # Vérifier que app.py existe
            app_path = "app.py"
            if getattr(sys, 'frozen', False):
                # En mode PyInstaller
                bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
                app_path = os.path.join(bundle_dir, "app.py")
            
            if not os.path.exists(app_path):
                logging.error(f"Fichier app.py introuvable: {app_path}")
                self.update_debug("app.py introuvable!")
                return
            
            logging.info(f"Utilisation du fichier app: {app_path}")
            
            # SOLUTION: Utiliser sys.executable avec streamlit_launcher.py pour éviter la boucle
            logging.info("Lancement de Streamlit via subprocess...")
            
            # Utiliser sys.executable avec l'argument streamlit_launcher.py
            # Ceci sera détecté par run_secure.py et lancera directement Streamlit
            cmd = [sys.executable, "streamlit_launcher.py", app_path]
            
            logging.info("Lancement de Streamlit via run_secure.py en mode Streamlit")
            
            # Variables d'environnement
            env = os.environ.copy()
            env['STREAMLIT_LAUNCHER_MODE'] = '1'  # Marqueur pour le launcher
            
            self.streamlit_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
            )
            
            logging.info(f"Processus Streamlit lancé: PID {self.streamlit_process.pid}")
            self.update_debug(f"Streamlit PID {self.streamlit_process.pid}")
            
            # Marquer comme démarré
            self.server_running = True
            
            # Attendre un peu
            import time
            time.sleep(2)
            
            # Vérifier que le processus est toujours en vie
            if self.streamlit_process.poll() is None:
                logging.info("Processus Streamlit stable")
            else:
                stdout, stderr = self.streamlit_process.communicate()
                logging.error(f"Streamlit s'est arrêté: stdout={stdout}, stderr={stderr}")
                self.server_running = False
        except Exception as e:
            logging.error(f"Erreur dans le thread Streamlit: {e}")
            self.update_debug(f"Erreur: {str(e)[:30]}")
            import traceback
            logging.error(traceback.format_exc())
        finally:
            logging.info("Thread Streamlit terminé")
            self.server_running = False
            
    def _check_server_startup(self):
        """Vérifier que le serveur a démarré et ouvrir le navigateur"""
        logging.info("Début de la vérification du démarrage du serveur...")
        max_attempts = 15
        
        for attempt in range(max_attempts):
            try:
                logging.info(f"Tentative {attempt + 1}/{max_attempts} de connexion au serveur...")
                self.root.after(0, lambda: self.update_debug(f"Vérification {attempt + 1}/{max_attempts}..."))
                
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 8501))
                sock.close()
                
                if result == 0:
                    # Serveur démarré
                    logging.info("Serveur Streamlit démarré avec succès!")
                    self.root.after(0, lambda: self.update_debug("Serveur démarré!"))
                    self.root.after(0, lambda: self.update_ui_state(True))
                    
                    # Ouvrir le navigateur
                    try:
                        webbrowser.open('http://localhost:8501')
                        logging.info("Navigateur ouvert sur http://localhost:8501")
                    except Exception as e:
                        logging.warning(f"Impossible d'ouvrir le navigateur: {e}")
                    
                    logging.info("=== FIN DÉMARRAGE DU SERVEUR (SUCCÈS) ===")
                    return
                    
            except Exception as e:
                logging.warning(f"Erreur lors de la vérification du serveur: {e}")
            
            time.sleep(2)
        
        # Échec du démarrage
        logging.error("Échec du démarrage du serveur - timeout atteint")
        self.root.after(0, lambda: self.update_debug("Échec démarrage!"))
        self.root.after(0, lambda: self.update_ui_state(False))
        logging.info("=== FIN DÉMARRAGE DU SERVEUR (ÉCHEC) ===")
    
    def stop_server(self):
        """Arrêter le serveur"""
        logging.info("=== DÉBUT ARRÊT DU SERVEUR ===")
        self.update_debug("Arrêt serveur...")
        
        try:
            # Arrêter d'abord notre propre processus s'il existe
            if self.streamlit_process and self.streamlit_process.poll() is None:
                logging.info(f"Arrêt du processus Streamlit géré: PID {self.streamlit_process.pid}")
                self.streamlit_process.terminate()
                
                try:
                    self.streamlit_process.wait(timeout=5)
                    logging.info("Processus géré arrêté proprement")
                except subprocess.TimeoutExpired:
                    logging.warning("Timeout - arrêt forcé du processus géré")
                    self.streamlit_process.kill()
                
                self.streamlit_process = None
            
            # Chercher et arrêter tous les autres processus Streamlit
            streamlit_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('streamlit' in str(arg).lower() for arg in cmdline):
                        if any('8501' in str(arg) for arg in cmdline):
                            streamlit_processes.append(proc)
                            logging.info(f"Processus Streamlit trouvé pour arrêt: PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Arrêter les processus trouvés
            for proc in streamlit_processes:
                try:
                    logging.info(f"Arrêt du processus PID {proc.pid}...")
                    proc.terminate()
                    
                    # Attendre que le processus se termine
                    try:
                        proc.wait(timeout=5)
                        logging.info(f"Processus PID {proc.pid} arrêté proprement")
                    except psutil.TimeoutExpired:
                        logging.warning(f"Timeout - arrêt forcé du processus PID {proc.pid}")
                        proc.kill()
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logging.warning(f"Impossible d'arrêter le processus: {e}")
            
            if not streamlit_processes and not self.streamlit_process:
                logging.info("Aucun processus Streamlit trouvé à arrêter")
                self.update_debug("Pas de processus trouvé")
            else:
                self.update_debug("Serveur arrêté")
        
        except Exception as e:
            logging.error(f"Erreur lors de l'arrêt du serveur: {e}")
            self.update_debug(f"Erreur arrêt: {e}")
        
        # Mettre à jour l'interface
        self.server_running = False
        self.update_ui_state(False)
        logging.info("=== FIN ARRÊT DU SERVEUR ===")
    
    def center_window(self):
        """Centrer la fenêtre sur l'écran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_closing(self):
        """Fermeture propre de l'application"""
        logging.info("Fermeture de l'application...")
        
        if self.server_running:
            result = messagebox.askyesnocancel(
                "Confirmation",
                "Le serveur OptimPV est en cours d'exécution.\n\n"
                "Voulez-vous l'arrêter avant de quitter?",
                icon='question'
            )
            
            if result is None:  # Cancel
                logging.info("Fermeture annulée par l'utilisateur")
                return
            elif result:  # Yes
                logging.info("Arrêt du serveur avant fermeture...")
                self.stop_server()
                time.sleep(1)
        
        logging.info("Fermeture de l'interface...")
        self.root.destroy()
    
    def run(self):
        """Lancer l'interface"""
        try:
            if Path("assets/icon.ico").exists():
                self.root.iconbitmap("assets/icon.ico")
        except Exception as e:
            logging.warning(f"Impossible de charger l'icône: {e}")
        
        logging.info("Démarrage de la boucle principale de l'interface...")
        self.update_debug("Interface prête")
        self.root.mainloop()
        logging.info("Interface fermée")

def main():
    """Point d'entrée principal"""
    try:
        logging.info("=== DÉMARRAGE OPTIMPV CONTROLLER ===")
        logging.info(f"Python: {sys.version}")
        logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
        if getattr(sys, 'frozen', False):
            logging.info(f"Executable: {sys.executable}")
            logging.info(f"Bundle dir: {getattr(sys, '_MEIPASS', 'N/A')}")
        
        app = OptimPVController()
        app.run()
    except Exception as e:
        logging.error(f"Erreur fatale: {e}", exc_info=True)
        messagebox.showerror(
            "Erreur Fatale",
            f"Une erreur critique s'est produite:\n\n{str(e)}\n\n"
            f"Consultez {LOG_FILE_PATH} pour plus de détails."
        )
        sys.exit(1)
    finally:
        logging.info("=== ARRÊT OPTIMPV CONTROLLER ===")

if __name__ == "__main__":
    # Support pour les processus gelés (frozen) - CRUCIAL pour PyInstaller
    multiprocessing.freeze_support()
    main()