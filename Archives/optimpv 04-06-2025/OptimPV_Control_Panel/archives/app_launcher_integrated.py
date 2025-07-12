# process/app_launcher_integrated.py
"""
Lanceur intégré - Lance app.py directement depuis l'exe
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

class IntegratedAppLauncher:
    def __init__(self):
        self.app_extracted = False
        self.temp_dir = None
    
    def launch_app(self, config):
        """Lancer app.py intégré dans l'exe"""
        try:
            # Si on est dans l'exe PyInstaller
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
                
                # Créer un répertoire temporaire
                self.temp_dir = tempfile.mkdtemp(prefix="optimv_")
                temp_path = Path(self.temp_dir)
                
                # Copier app.py et les modules associés
                app_path = base_path / "app.py"
                if app_path.exists():
                    shutil.copy2(app_path, temp_path / "app.py")
                
                # Copier les dossiers modules, data, config s'ils existent
                for folder in ['modules', 'data', 'config']:
                    src_folder = base_path / folder
                    if src_folder.exists():
                        shutil.copytree(src_folder, temp_path / folder)
                
                # Lancer depuis le répertoire temporaire
                os.chdir(temp_path)
                
            else:
                # Mode développement - chercher app.py dans le parent
                app_path = Path(__file__).parent.parent.parent / "app.py"
                if not app_path.exists():
                    raise FileNotFoundError(f"app.py non trouvé: {app_path}")
                os.chdir(app_path.parent)
            
            # Lancer Streamlit
            cmd = [
                sys.executable,
                '-m', 'streamlit', 'run',
                'app.py',
                '--server.port', str(config.get('port', 8501)),
                '--server.address', config.get('bind_address', '127.0.0.1'),
                '--server.headless', 'true'
            ]
            
            # Exécuter et attendre
            process = subprocess.Popen(cmd)
            process.wait()
            
        finally:
            # Nettoyer le répertoire temporaire
            if self.temp_dir and Path(self.temp_dir).exists():
                import shutil
                shutil.rmtree(self.temp_dir)
    
    def terminate_app(self, graceful=True):
        """Arrêter l'application"""
        # Nettoyer si nécessaire
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)
        return True

import shutil