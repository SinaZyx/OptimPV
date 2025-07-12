import json
import os

# Tentative d'import du PathManager et du logger global
# Ces dépendances sont importantes pour ConfigManager
try:
    from .path_manager import PathManager
except ImportError:
    # Si PathManager n'est pas directement importable (ex: structure de dossier différente ou test unitaire direct)
    # On essaie un import relatif plus générique ou on signale l'erreur.
    # Pour ce cas, on va supposer qu'il est au même niveau dans 'core' ou un niveau au-dessus.
    try:
        from path_manager import PathManager # Si core est dans PYTHONPATH
    except ImportError:
        # Fallback très basique si PathManager n'est pas trouvé
        # Cela limitera sévèrement les capacités de ConfigManager
        print("CRITICAL WARNING: ConfigManager could not import PathManager. Path resolution will be impaired.")
        class FallbackPathManager:
            @staticmethod
            def get_config_file(filename):
                # Comportement très basique: chercher dans le répertoire courant seulement
                print(f"FallbackPathManager: Looking for {filename} in current directory only.")
                return filename 
        PathManager = FallbackPathManager()

try:
    from optimpv_main import logger
except (ImportError, ModuleNotFoundError):
    import tempfile, time
    class FallbackConfigLogger:
        def __init__(self, filepath):
            self.filepath = filepath
            self._log(f"=== FallbackConfigLogger Initialized ({time.time()}) ===", "INFO")
        def _log(self, msg, level):
            formatted_msg = f"[{level}] {time.strftime('%Y-%m-%d %H:%M:%S')}: {msg}"
            print(formatted_msg)
            try:
                with open(self.filepath, 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_msg}\n")
                    f.flush()
            except Exception as e:
                print(f"FallbackConfigLogger: Failed to write to log file {self.filepath}: {e}")
        def write(self, msg, level="INFO"): self._log(msg, level)
        def info(self, msg): self._log(msg, "INFO")
        def warning(self, msg): self._log(msg, "WARNING")
        def error(self, msg): self._log(msg, "ERROR")
        def debug(self, msg): self._log(msg, "DEBUG")
    logger = FallbackConfigLogger(os.path.join(tempfile.gettempdir(), f"configmanager_fallback_{os.getpid()}.log"))
    logger.info("ConfigManager: Global logger or PathManager not fully resolved. Using fallbacks.")

class ConfigManager:
    """Gestionnaire unique pour toutes les configs.
       Utilise le PathManager pour localiser les fichiers de configuration."""
    
    _instance = None
    _configs = {} # Dictionnaire pour stocker les configurations chargées
    _default_configs = { # Configurations par défaut si les fichiers ne sont pas trouvés
        "network": {"default_host": "localhost", "default_port": 8501},
        "license": {"status": "unlicensed", "key": None},
        "security": {"usb_drive_letter": "G", "token_file_name": "sys.dat"},
        # Ajoutez d'autres configurations par défaut ici
        "app_settings": {"theme": "dark", "language": "fr"}
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            logger.info("ConfigManager: Creating new instance.")
            cls._instance = super().__new__(cls)
            # Initialisation unique lors de la création de la première instance
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, force_reload=False):
        """Initialise le ConfigManager. Charge les configurations si ce n'est pas déjà fait ou si force_reload est True."""
        if self._initialized and not force_reload:
            logger.debug("ConfigManager: Already initialized. Skipping redundant load.")
            return
        
        logger.info(f"ConfigManager: Initializing (force_reload={force_reload}). Loading all configurations...")
        self._configs = {} # Réinitialiser si on force le rechargement
        self._load_all_configs()
        self._initialized = True
        logger.info("ConfigManager: Initialization complete.")

    def _load_json_config(self, config_name: str, filename: str):
        """Charge un fichier de configuration JSON spécifique.
           Utilise PathManager pour trouver le fichier et gère les erreurs de chargement.
           Retourne le contenu du JSON ou la configuration par défaut en cas d'échec.
        """
        logger.debug(f"ConfigManager: Attempting to load JSON config '{config_name}' from '{filename}'...")
        try:
            # Utiliser PathManager pour obtenir le chemin complet du fichier de configuration
            config_path = PathManager.get_config_file(filename)
            logger.info(f"ConfigManager: Resolved path for '{filename}': {config_path}")

            if config_path and config_path.exists() and config_path.is_file():
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    logger.info(f"ConfigManager: Successfully loaded '{config_name}' from {config_path}.")
                    return loaded_config
            else:
                logger.warning(f"ConfigManager: Config file '{filename}' not found at {config_path} or is not a file.")
        except json.JSONDecodeError as e:
            logger.error(f"ConfigManager: Error decoding JSON from '{filename}' (path: {config_path}): {e}. Using default for '{config_name}'.")
        except Exception as e:
            logger.error(f"ConfigManager: Failed to load '{config_name}' from '{filename}' (path: {config_path}): {e}. Using default.")
        
        # Si le chargement échoue ou le fichier n'existe pas, retourner la config par défaut pour ce nom
        default_config = self._default_configs.get(config_name, {})
        logger.warning(f"ConfigManager: Using default configuration for '{config_name}': {default_config}")
        return default_config

    def _load_all_configs(self):
        """Charge toutes les configurations définies au démarrage."""
        logger.info("ConfigManager: Loading all defined configurations...")
        # Charger network_admin_config.json dans self._configs['network']
        self._configs['network'] = self._load_json_config('network', 'network_admin_config.json')
        
        # Charger license.json dans self._configs['license']
        self._configs['license'] = self._load_json_config('license', 'license.json')
        
        # Charger security_config.json dans self._configs['security'] (exemple)
        self._configs['security'] = self._load_json_config('security', 'security_config.json')

        # Charger app_settings.json dans self._configs['app_settings'] (exemple)
        self._configs['app_settings'] = self._load_json_config('app_settings', 'app_settings.json')
        
        logger.info(f"ConfigManager: All configurations loaded. Current configs: {list(self._configs.keys())}")
        logger.debug(f"ConfigManager: Loaded config content (sample - network): {self._configs.get('network')}")

    def get_config(self, config_name: str):
        """Récupère une configuration par son nom.
           Retourne la configuration chargée ou la configuration par défaut si non trouvée.
        """
        if not self._initialized:
            logger.warning("ConfigManager: Accessed get_config before full initialization. Consider calling load_all_configs() or ensuring __init__ runs.")
            # Forcer une initialisation si elle n'a pas eu lieu (peut arriver si on accède à l'instance avant __init__)
            self.__init__() 

        config = self._configs.get(config_name)
        if config is not None:
            logger.debug(f"ConfigManager: Retrieved config '{config_name}'.")
            return config
        else:
            logger.warning(f"ConfigManager: Config '{config_name}' not found in loaded configs. Checking defaults.")
            default_config = self._default_configs.get(config_name, {})
            if default_config:
                 logger.info(f"ConfigManager: Returning default config for '{config_name}'.")
            else:
                 logger.error(f"ConfigManager: No loaded or default config found for '{config_name}'. Returning empty dict.")
            return default_config

    def reload_all_configs(self):
        """Force le rechargement de toutes les configurations depuis les fichiers."""
        logger.info("ConfigManager: Force reloading all configurations...")
        self.__init__(force_reload=True)

    def get_all_configs(self):
        """Retourne un dictionnaire de toutes les configurations chargées."""
        if not self._initialized: self.__init__()
        return self._configs.copy() # Retourner une copie pour éviter la modification externe

# Exemple d'utilisation et de test
if __name__ == "__main__":
    logger.info("\n--- Testing ConfigManager --- ")

    # Création/Accès à l'instance singleton
    config_manager1 = ConfigManager() # Devrait initialiser et charger
    config_manager2 = ConfigManager() # Devrait retourner la même instance, sans recharger par défaut

    logger.info(f"Instance 1 ID: {id(config_manager1)}")
    logger.info(f"Instance 2 ID: {id(config_manager2)}")
    assert id(config_manager1) == id(config_manager2), "ConfigManager should be a singleton!"

    # Accéder à des configurations (elles utiliseront les valeurs par défaut si les fichiers n'existent pas)
    logger.info("--- Accessing Configurations ---")
    network_config = config_manager1.get_config('network')
    logger.info(f"Network Config: {network_config}")

    license_config = config_manager1.get_config('license')
    logger.info(f"License Config: {license_config}")

    security_config = config_manager1.get_config('security')
    logger.info(f"Security Config: {security_config}")
    
    non_existent_config = config_manager1.get_config('non_existent')
    logger.info(f"Non-existent Config (should be empty or default if defined): {non_existent_config}")

    all_cfgs = config_manager1.get_all_configs()
    logger.info(f"All loaded configs: {all_cfgs}")

    # Simuler la création d'un fichier de configuration pour tester le chargement
    logger.info("--- Testing with a dummy config file ---")
    dummy_network_file_name = "network_admin_config.json"
    # PathManager devrait le placer à la racine du projet par défaut s'il ne le trouve pas ailleurs.
    # Pour ce test, nous allons le créer manuellement dans le répertoire courant pour simplicité,
    # en supposant que PathManager.get_config_file le trouvera là en premier s'il est exécuté ici.
    
    # Déterminer où PathManager chercherait le fichier. Pour un test direct, cela peut être complexe.
    # Le plus simple est de s'assurer que get_config_file du PathManager (ou son fallback) le trouve.
    # Si on utilise le FallbackPathManager, il cherchera dans le dossier courant.
    current_dir_dummy_path = PathManager.get_config_file(dummy_network_file_name)
    is_fallback_pm = isinstance(PathManager, type(FallbackPathManager()))
    
    # Si c'est le fallback PM, le chemin sera juste le nom du fichier.
    # Sinon, on espère que `get_config_file` a une logique qui inclut le dossier courant pour le test.
    # Pour un test robuste, il faudrait mocker PathManager ou s'assurer que `get_config_file` pointe vers un endroit contrôlable.
    
    # Pour ce test, créons-le simplement s'il utilise le fallback path ou si le chemin résolu est local
    # Attention: cela suppose que `get_config_file` résoudra à un chemin local pour ce test.
    # Une meilleure approche pour les tests unitaires serait de mocker `PathManager.get_config_file`.
    
    # Créons un fichier network_admin_config.json DANS LE DOSSIER COURANT pour ce test
    # Cette approche est simple mais dépend de la logique de PathManager.get_config_file
    # pour le trouver (surtout si elle priorise le dossier courant en dev/test).
    dummy_content = {"host": "127.0.0.1", "port": 8888, "source": "dummy_test_file"}
    created_dummy = False
    # On va essayer de créer le fichier là où PathManager le chercherait en premier ou dans le cwd
    # La logique de PathManager.get_config_file est: app_root/filename, app_root/config/filename, home, appdata.
    # Pour un test simple, plaçons-le à la racine (simulée par cwd ici si __file__ n'est pas défini comme dans un script normal)
    
    # Utilisons le premier chemin que PathManager propose pour créer le fichier de test
    # (en espérant qu'il soit accessible en écriture)
    path_to_create_dummy = PathManager.get_config_file(dummy_network_file_name) 
    # Si get_config_file retourne un chemin qui existe déjà (ex: un fichier de config réel), ce test peut être problématique.
    # Pour un test propre, il faudrait un nom de fichier unique pour le test.
    
    # Pour simplifier, on crée le fichier dans le dossier courant SI le PathManager le cherche là en premier
    # ou si get_app_root est le dossier courant (cas des tests unitaires parfois)
    # Ce test est un peu fragile à cause de la dépendance à PathManager.
    
    # Tentons de créer un fichier de test dans le répertoire courant.
    # PathManager DEVRAIT le trouver s'il est configuré pour chercher aussi localement.
    # (ou si get_app_root pointe ici).
    test_config_path = "network_admin_config.json" # Nom simple pour le test
    if not os.path.exists(test_config_path):
        try:
            with open(test_config_path, 'w') as f_dummy:
                json.dump(dummy_content, f_dummy)
            logger.info(f"Created dummy config file: {test_config_path} with content: {dummy_content}")
            created_dummy = True
        except Exception as e:
            logger.error(f"Could not create dummy config file at {test_config_path} for testing: {e}")

    # Recharger les configurations pour prendre en compte le nouveau fichier
    if created_dummy:
        logger.info("--- Reloading configs to pick up dummy file ---")
        config_manager1.reload_all_configs()
        network_config_reloaded = config_manager1.get_config('network')
        logger.info(f"Network Config after reload (should pick up dummy if PathManager finds it): {network_config_reloaded}")
        if network_config_reloaded.get("source") == "dummy_test_file":
            logger.info("SUCCESS: Dummy config file was loaded.")
        else:
            logger.warning("NOTE: Dummy config file was NOT loaded. Check PathManager logic or test file location.")
            logger.warning(f"PathManager searched for {dummy_network_file_name} and would use: {PathManager.get_config_file(dummy_network_file_name)}")

        # Nettoyage du fichier dummy
        try:
            os.remove(test_config_path)
            logger.info(f"Cleaned up dummy config file: {test_config_path}")
        except OSError as e:
            logger.error(f"Error removing dummy config file {test_config_path}: {e}")
    else:
        logger.warning("Skipped testing with dummy file as it could not be created or PathManager path was not local.")

    logger.info("--- ConfigManager Test Complete ---") 