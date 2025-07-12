import os
import sys
from pathlib import Path

class PathManager:
    """Gestionnaire centralisé des chemins pour DEV et EXE"""
    
    @staticmethod
    def get_app_root():
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Cas d'un exécutable PyInstaller
            return Path(sys._MEIPASS)
        # Cas d'un script Python ou répertoire de développement
        # On remonte de plusieurs niveaux depuis ce fichier pour atteindre la racine du projet
        # path_manager.py -> core -> server_control -> Interface serveur -> RACINE_PROJET
        return Path(__file__).resolve().parent.parent.parent.parent
    
    @staticmethod
    def get_security_dir():
        return PathManager.get_app_root() / "Interface serveur" / "server_control" / "security"
    
    @staticmethod
    def get_config_file(filename):
        # Chercher dans plusieurs emplacements par ordre de priorité
        app_root = PathManager.get_app_root()
        
        locations = []
        
        # 1. Dans la racine de l'application (pour EXE ou DEV)
        locations.append(app_root / filename)
        
        # 2. Dans un sous-dossier 'config' à la racine (pratique en DEV)
        locations.append(app_root / "config" / filename)
        
        # 3. Configuration utilisateur spécifique à OptimPV
        try:
            home_config = Path.home() / ".optimpv" / filename
            locations.append(home_config)
        except RuntimeError: # Peut arriver si home() n'est pas accessible
            pass

        # 4. Configuration dans APPDATA (Windows)
        appdata_dir = os.environ.get('APPDATA', '')
        if appdata_dir:
            optimpv_appdata_config = Path(appdata_dir) / 'OptimPV' / filename
            locations.append(optimpv_appdata_config)
            
        logger.write(f"[PathManager] Searching for {filename} in: {locations}")

        for loc in locations:
            if loc.exists():
                logger.write(f"[PathManager] Found {filename} at: {loc}")
                return loc
        
        logger.write(f"[PathManager] {filename} not found in any predefined location. Defaulting to: {locations[0]}")
        return locations[0]  # Par défaut (le premier chemin de la liste)

# Ajout d'un logger simple pour ce module aussi, s'il est utilisé indépendamment
# ou si le logger principal n'est pas encore disponible.
# Dans une application réelle, ce logger serait configuré de manière plus globale.
if __name__ == '__main__':
    # Pour les tests directs de ce module
    import tempfile
    import time
    
    class SimpleLogger:
        def __init__(self, filepath):
            self.filepath = filepath
            self.write(f"=== PathManager TEST {time.time()} ===")
        
        def write(self, msg):
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(f"{msg}\n")
                f.flush()
            print(msg)
            
    log_file_path = os.path.join(tempfile.gettempdir(), f"path_manager_test_{os.getpid()}.log")
    logger = SimpleLogger(log_file_path)

    logger.write("Testing PathManager...")
    logger.write(f"App Root: {PathManager.get_app_root()}")
    logger.write(f"Security Dir: {PathManager.get_security_dir()}")
    
    # Test avec un fichier de configuration fictif
    dummy_config_name = "test_config.json"
    # Créez un fichier fictif pour tester la découverte
    # (PathManager.get_app_root() / dummy_config_name).touch() # Décommentez pour tester la découverte
    logger.write(f"Config File ({dummy_config_name}): {PathManager.get_config_file(dummy_config_name)}")
    
    # Test avec un fichier dans le sous-dossier config
    dummy_config_in_subdir_name = "another_config.json"
    config_subdir = PathManager.get_app_root() / "config"
    # config_subdir.mkdir(exist_ok=True)
    # (config_subdir / dummy_config_in_subdir_name).touch() # Décommentez pour tester
    logger.write(f"Config File (in config/ subdir): {PathManager.get_config_file(dummy_config_in_subdir_name)}")

    # Assurez-vous que le logger global de optimpv_main est disponible si ce module est importé
else:
    # Si ce module est importé, nous supposons que le logger de optimpv_main.py est déjà configuré
    # et est accessible globalement. Si ce n'est pas le cas, il faudrait le passer en argument
    # ou utiliser une autre méthode de partage de logger.
    # Pour l'instant, on essaie de l'importer.
    try:
        # Essayons d'importer le logger déjà configuré dans optimpv_main
        # Cela crée une dépendance cyclique potentielle si PathManager est importé TRES TOT
        # dans optimpv_main.py avant que logger ne soit défini.
        # Une meilleure solution serait d'injecter le logger ou d'utiliser le module logging standard.
        from optimpv_main import logger as global_logger
        logger = global_logger
    except ImportError:
        # Fallback sur un logger basique si l'import échoue (par exemple, lors de tests unitaires de ce module seul)
        import tempfile
        import time
        class FallbackLogger:
            def __init__(self, filepath):
                self.filepath = filepath
                self.write(f"=== PathManager Fallback Logger {time.time()} ===")
            def write(self, msg):
                with open(self.filepath, 'a', encoding='utf-8') as f:
                    f.write(f"{msg}\n")
                    f.flush()
                print(f"FallbackLogger: {msg}")
        log_file_path = os.path.join(tempfile.gettempdir(), f"path_manager_fallback_{os.getpid()}.log")
        logger = FallbackLogger(log_file_path)
        logger.write("Failed to import global_logger from optimpv_main, using FallbackLogger.") 