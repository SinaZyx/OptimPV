import sys
import os
from datetime import datetime

# Redirection simple des logs
log_file = os.path.join(os.path.dirname(sys.executable), 'OptimPV_startup.log')
with open(log_file, 'a', encoding='utf-8') as f:
    f.write(f"\n{'='*60}\n")
    f.write(f"OptimPV Control Panel - {datetime.now()}\n")
    f.write(f"Python {sys.version}\n")
    f.write(f"Executable: {sys.executable}\n")
    f.write(f"Working directory: {os.getcwd()}\n")
    f.write(f"{'='*60}\n")

# Rediriger stdout/stderr vers le fichier log
class LogRedirector:
    def __init__(self, filename):
        self.file = open(filename, 'a', encoding='utf-8')
    
    def write(self, message):
        self.file.write(message)
        self.file.flush()
    
    def flush(self):
        self.file.flush()

sys.stdout = LogRedirector(log_file)
sys.stderr = sys.stdout

print("\nDémarrage OptimPV Control Panel...")
print(f"Répertoire de travail: {os.getcwd()}")

try:
    print("\nImport de main_entry...")
    import main_entry
    
    print("Lancement de main()...")
    main_entry.main()
    
except Exception as e:
    import traceback
    print(f"\n{'!'*60}")
    print("ERREUR FATALE:")
    print(f"{'!'*60}")
    print(f"Erreur: {str(e)}")
    traceback.print_exc()
    print(f"\n{'!'*60}")
    print("\nVérifiez le fichier OptimPV_startup.log pour plus de détails.")
    
    # En mode console, on peut afficher une pause
    try:
        input("\nAppuyez sur Entrée pour fermer...")
    except:
        pass  # En cas d'erreur même sur input
        
print("\nFin du programme OptimPV Control Panel.")