# Ce fichier est un exemple de hook runtime pour PyInstaller.
# Il peut être utilisé pour exécuter du code au démarrage de l'application packagée,
# avant même que le script principal ne soit lancé.
# Utile pour configurer des variables d'environnement, des chemins, etc.

# import os
# import sys

# print("RUNTIME HOOK: Hello from runtime_hook.py!")

# Exemple: Modifier sys.path ou une variable d'environnement
# if getattr(sys, 'frozen', False):
#     # Ce code s'exécute uniquement dans l'environnement packagé
#     application_path = sys._MEIPASS # Chemin vers le dossier temporaire de l'EXE
#     print(f"RUNTIME HOOK: Application path (MEIPASS): {application_path}")
    
    # Ajouter un chemin spécifique à sys.path si nécessaire
    # custom_lib_path = os.path.join(application_path, 'my_custom_libs')
    # if custom_lib_path not in sys.path:
    #     sys.path.insert(0, custom_lib_path)
    #     print(f"RUNTIME HOOK: Added {custom_lib_path} to sys.path")

# print("RUNTIME HOOK: End of runtime_hook.py") 