# Runtime hook pour corriger l'erreur 'obj' dans scipy._distn_infrastructure
import sys

def patch_scipy_obj_error():
    """
    Patch scipy._distn_infrastructure pour corriger l'erreur 'obj' not defined
    Ce hook s'execute avant l'importation de scipy
    """
    import importlib.util
    import types
    
    # Intercepter l'importation de scipy.stats._distn_infrastructure
    original_import = __builtins__.__import__
    
    def patched_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'scipy.stats._distn_infrastructure' or (isinstance(fromlist, (list, tuple)) and 'scipy.stats._distn_infrastructure' in str(fromlist)):
            # Importer normalement d'abord
            module = original_import(name, globals, locals, fromlist, level)
            
            # Si c'est le module _distn_infrastructure, on s'assure que obj existe
            if hasattr(module, '_distn_infrastructure') or name.endswith('_distn_infrastructure'):
                target_module = module._distn_infrastructure if hasattr(module, '_distn_infrastructure') else module
                if not hasattr(target_module, 'obj'):
                    target_module.obj = object()
            
            return module
        
        return original_import(name, globals, locals, fromlist, level)
    
    # Remplacer temporairement __import__
    __builtins__.__import__ = patched_import

# Appliquer le patch immediatement
patch_scipy_obj_error() 