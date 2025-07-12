#!/usr/bin/env python3
"""
Test pour voir si le fonds de réserve cause le problème d'optimisation
"""

import sys
import os

# Ajouter le chemin des modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

def patch_disable_sinking_fund():
    """Désactive temporairement le fonds de réserve pour tester"""
    
    print("🔧 PATCH TEMPORAIRE - DÉSACTIVER FONDS DE RÉSERVE")
    print("=" * 55)
    
    # Lire le fichier core_analyzer.py
    core_analyzer_path = "modules/engine_module/core_analyzer.py"
    
    try:
        with open(core_analyzer_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher la section du fonds de réserve
        marker_start = "# === GESTION DU FONDS DE RÉSERVE ONDULEUR (SINKING FUND) ==="
        marker_end = "# Appliquer la logique de placement de trésorerie"
        
        if marker_start in content:
            print("✅ Section fonds de réserve trouvée")
            
            # Créer une version commentée
            content_patched = content.replace(
                marker_start,
                "# === GESTION DU FONDS DE RÉSERVE ONDULEUR (SINKING FUND) === [TEMPORAIREMENT DÉSACTIVÉ]"
            )
            
            # Trouver et commenter la logique
            start_idx = content_patched.find(marker_start.replace("===", "=== [TEMPORAIREMENT DÉSACTIVÉ]"))
            if start_idx != -1:
                # Chercher la fin de la section
                lines = content_patched[start_idx:].split('\n')
                patched_lines = []
                in_sinking_fund = True
                indent_level = None
                
                for line in lines:
                    if marker_end in line:
                        in_sinking_fund = False
                        patched_lines.append(line)
                        continue
                    
                    if in_sinking_fund:
                        if line.strip().startswith('if ') and 'OPEX_Provision_Onduleur_Mensuel' in line:
                            # Commenter la condition principale
                            if indent_level is None:
                                indent_level = len(line) - len(line.lstrip())
                            patched_lines.append(' ' * indent_level + '# ' + line.strip() + ' # [DÉSACTIVÉ POUR TEST]')
                        elif line.strip() and (line.startswith('            ') or line.startswith('                ')):
                            # Commenter le contenu de la condition
                            patched_lines.append(' ' * indent_level + '# ' + line.strip())
                        else:
                            patched_lines.append(line)
                    else:
                        patched_lines.append(line)
                
                # Reconstruire le contenu
                content_before = content_patched[:start_idx]
                content_after = '\n'.join(patched_lines[1:])  # Exclure la première ligne déjà modifiée
                content_patched = content_before + '\n'.join(patched_lines)
            
            # Sauvegarder le patch
            patch_path = "core_analyzer_no_sinking_fund.py"
            with open(patch_path, 'w', encoding='utf-8') as f:
                f.write(content_patched)
            
            print(f"✅ Patch créé: {patch_path}")
            print("\n💡 INSTRUCTIONS:")
            print("1. Sauvegardez votre core_analyzer.py original")
            print("2. Remplacez-le temporairement par le patch")
            print("3. Testez l'optimisation LCOE")
            print("4. Si ça marche → Le problème vient du fonds de réserve")
            print("5. Si ça ne marche toujours pas → Le problème est ailleurs")
            
            return True
            
        else:
            print("❌ Section fonds de réserve non trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du patch: {e}")
        return False

if __name__ == "__main__":
    success = patch_disable_sinking_fund()
    
    if success:
        print(f"\n🎯 TEST À EFFECTUER:")
        print(f"Utilisez le fichier patché pour voir si l'optimisation fonctionne sans le fonds de réserve.")
    else:
        print(f"\n⚠️  Impossible de créer le patch automatiquement.")
        print(f"Commentez manuellement la section du fonds de réserve dans core_analyzer.py")