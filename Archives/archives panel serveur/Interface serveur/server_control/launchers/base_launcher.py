from abc import ABC, abstractmethod

# Tentative d'import du logger global, sinon fallback
try:
    from optimpv_main import logger
except (ImportError, ModuleNotFoundError):
    # En cas d'échec (ex: tests unitaires, ou si ce module est chargé avant optimpv_main.logger)
    # On crée un logger basique pour ce module.
    import logging
    import tempfile
    import os
    import time
    
    temp_log_file = os.path.join(tempfile.gettempdir(), f"baselauncher_fallback_{os.getpid()}.log")
    
    class FallbackLauncherLogger:
        def __init__(self, filepath):
            self.filepath = filepath
            self.log_message(f"=== FallbackLauncherLogger Initialized ({time.time()}) ===")

        def log_message(self, msg, level="INFO"):
            # Simule les niveaux INFO et ERROR pour la sortie console/fichier
            formatted_msg = f"[{level}] {msg}"
            print(formatted_msg) # Sortie console
            try:
                with open(self.filepath, 'a', encoding='utf-8') as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {formatted_msg}\n")
                    f.flush()
            except Exception as e:
                print(f"FallbackLauncherLogger: Failed to write to log file {self.filepath}: {e}")

        def info(self, msg):
            self.log_message(msg, "INFO")

        def error(self, msg):
            self.log_message(msg, "ERROR")
            
        def debug(self, msg):
            self.log_message(msg, "DEBUG")
            
        def warning(self, msg):
            self.log_message(msg, "WARNING")

        # Alias pour write si on veut utiliser la même interface que le logger de optimpv_main
        def write(self, msg):
            self.info(msg)
            
    logger = FallbackLauncherLogger(temp_log_file)
    logger.info("BaseLauncher: Global logger from optimpv_main not found. Using FallbackLauncherLogger.")

# Tentative d'import du SecurityManager ou d'une classe de base si elle existe
# Pour l'instant, on va juste définir un placeholder.
# Dans l'idéal, SecurityManager serait aussi une classe bien définie et importable.
class PlaceholderSecurityManager:
    def __init__(self):
        logger.info("PlaceholderSecurityManager initialized. Replace with actual security manager.")
        # Initialiser les vrais mécanismes de sécurité ici
        pass

    def check_all_protections(self) -> bool:
        logger.info("PlaceholderSecurityManager: Checking all protections (simulation)...")
        # Logique pour vérifier toutes les protections (USB, licence, etc.)
        return True # Simule que tout est OK

    def apply_pre_launch_security(self):
        logger.info("PlaceholderSecurityManager: Applying pre-launch security measures (simulation)...")
        # Par exemple, vérifier la licence avant de lancer l'application principale
        pass

class BaseLauncher(ABC):
    """Classe de base pour tous les lanceurs"""
    
    def __init__(self):
        self.logger = self._init_logger()
        self.logger.info(f"BaseLauncher initialized for {self.__class__.__name__}")
        self.security_manager = self._init_security() # Initialisation de la sécurité
    
    @abstractmethod
    def launch(self):
        """Méthode principale à implémenter par chaque lanceur spécifique."""
        pass
    
    def _init_logger(self):
        """Initialisation du logger. Utilise le logger global si disponible."""
        # Le logger est déjà défini en haut du module (soit global, soit fallback)
        return logger

    def _init_security(self):
        """Initialisation commune de la sécurité.
        Retourne une instance du gestionnaire de sécurité.
        """
        self.logger.info("BaseLauncher: Initializing security manager...")
        # Ici, vous instancieriez votre vrai SecurityManager
        # Exemple : from ..security.security_manager import SecurityManager
        # return SecurityManager()
        # Pour l'instant, on utilise le placeholder :
        return PlaceholderSecurityManager()
    
    def _handle_error(self, error_message: str, exception_obj: Optional[Exception] = None):
        """Gestion centralisée des erreurs pour les lanceurs."""
        full_message = f"ERROR in {self.__class__.__name__}: {error_message}"
        if exception_obj:
            # Idéalement, on utiliserait traceback.format_exc() pour obtenir la stack trace
            # Mais pour garder simple, on convertit juste l'exception en chaîne.
            full_message += f" | Exception: {str(exception_obj)}"
        
        self.logger.error(full_message)
        
        # Logique de notification utilisateur, si nécessaire
        # Par exemple, afficher une boîte de dialogue d'erreur ou écrire dans un log d'erreurs spécifique.
        print(f"CRITICAL LAUNCHER ERROR: {full_message}") # Assurer une sortie console en cas d'échec du logger
        
        # On pourrait aussi vouloir arrêter l'application ici ou prendre d'autres mesures
        # sys.exit(1) # Optionnel, dépend de la criticité

    def run_pre_launch_checks(self):
        """Exécute les vérifications de sécurité avant le lancement."""
        self.logger.info(f"{self.__class__.__name__}: Running pre-launch security checks...")
        self.security_manager.apply_pre_launch_security()
        if not self.security_manager.check_all_protections():
            error_msg = "Pre-launch security checks failed!"
            self.logger.error(error_msg)
            self._handle_error(error_msg)
            # Il faudrait peut-être empêcher le lancement ici
            raise RuntimeError("Security checks failed, aborting launch.")
        self.logger.info(f"{self.__class__.__name__}: Pre-launch security checks passed.")

# Exemple d'utilisation (pourrait être dans un autre fichier)
if __name__ == "__main__":

    class MyStreamlitLauncher(BaseLauncher):
        def __init__(self):
            super().__init__() # Important d'appeler le constructeur de la classe de base
            self.streamlit_app_path = "app.py" # Chemin vers votre application Streamlit

        def launch(self):
            self.logger.info(f"MyStreamlitLauncher: Attempting to launch Streamlit app: {self.streamlit_app_path}")
            try:
                self.run_pre_launch_checks() # Exécuter les vérifications
                
                # Logique de lancement de Streamlit
                # import subprocess
                # process = subprocess.Popen(["streamlit", "run", self.streamlit_app_path])
                # process.wait()
                self.logger.info(f"MyStreamlitLauncher: Streamlit app {self.streamlit_app_path} would be launched here.")
                # Simuler un lancement réussi
                return True
            except RuntimeError as e:
                # Erreurs des pre_launch_checks sont déjà loggées par _handle_error via run_pre_launch_checks
                self.logger.error(f"MyStreamlitLauncher: Launch aborted due to security check failure: {e}")
                return False
            except Exception as e:
                self._handle_error(f"Failed to launch Streamlit app {self.streamlit_app_path}", e)
                return False

    # Test
    logger.info("\n--- Testing BaseLauncher --- ") # Logger du module, pas de la classe
    launcher = MyStreamlitLauncher()
    if launcher.launch():
        logger.info("MyStreamlitLauncher: Launch simulation successful.")
    else:
        logger.error("MyStreamlitLauncher: Launch simulation failed.")

    # Test avec un PlaceholderSecurityManager qui échoue (pour voir le _handle_error)
    class FailingSecurityManager(PlaceholderSecurityManager):
        def check_all_protections(self) -> bool:
            logger.warning("FailingSecurityManager: Simulating failed security check.")
            return False
            
    class MyLauncherWithFailingSecurity(MyStreamlitLauncher):
        def _init_security(self):
            self.logger.info("MyLauncherWithFailingSecurity: Initializing with FailingSecurityManager.")
            return FailingSecurityManager()
            
    logger.info("\n--- Testing BaseLauncher with Failing Security --- ")
    failing_launcher = MyLauncherWithFailingSecurity()
    if failing_launcher.launch():
        logger.info("MyLauncherWithFailingSecurity: Launch simulation successful (UNEXPECTED).")
    else:
        logger.error("MyLauncherWithFailingSecurity: Launch simulation failed as expected due to security.") 