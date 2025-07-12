from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

def patch_distn_infrastructure_source():
    """
    Patch le code source de _distn_infrastructure pour resoudre l'erreur 'obj'
    """
    try:
        import scipy.stats._distn_infrastructure
        module_file = scipy.stats._distn_infrastructure.__file__
        
        if module_file and os.path.exists(module_file):
            with open(module_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher la ligne problematique "del obj"
            if 'del obj' in content:
                # Remplacer par une version securisee
                patched_content = content.replace(
                    'del obj',
                    'if "obj" in locals(): del obj'
                )
                
                # Ecrire le fichier patche
                with open(module_file, 'w', encoding='utf-8') as f:
                    f.write(patched_content)
                    
                print(f"PATCH APPLIED: {module_file}")
    except Exception as e:
        print(f"PATCH FAILED: {e}")

# Appliquer le patch
patch_distn_infrastructure_source()

# Hook standard
datas = collect_data_files('scipy.stats')
hiddenimports = collect_submodules('scipy.stats') 