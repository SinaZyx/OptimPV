#!/usr/bin/env python3
"""
Analyse des problèmes de storage identifiés par l'utilisateur
"""

print("=== ANALYSE DES PROBLÈMES DE STORAGE ===")
print()

print("🔍 PROBLÈME 1: État des projets incorrect")
print("-" * 40)
print("SYMPTÔME: Les deux projets affichent Monte Carlo fait alors que c'est faux")
print("CAUSE PROBABLE: calculate_completeness_score() utilise la présence de clés plutôt que leur contenu")
print()
print("CODE ACTUEL:")
print("  'monte_carlo_done': 'monte_carlo_results' in st.session_state")
print()
print("PROBLÈME: Même si monte_carlo_results = {}, la clé existe donc retourne True")
print("SOLUTION: Vérifier que le dictionnaire n'est pas vide")
print()

print("🔍 PROBLÈME 2: Comparaison économique ne fonctionne pas") 
print("-" * 50)
print("SYMPTÔME: 'Aucune analyse économique' alors que ça a été fait")
print("CAUSE PROBABLE: compare_projects_advanced() charge les fichiers mais compare_projects_data est vide")
print()
print("FLUX:")
print("1. compare_projects_advanced() charge economic_results.json")
print("2. Mais la condition 'if not economic1 or not economic2' retourne True")
print("3. Soit les fichiers sont vides, soit ne se chargent pas")
print()

print("🔍 PROBLÈME 3: Logique de détection incohérente")
print("-" * 45)
print("Il y a DEUX endroits qui détectent l'état:")
print("1. calculate_completeness_score() - pour l'affichage des badges")
print("2. has_*_results dans save_current_project() - pour les flags manifest")
print()
print("CES DEUX LOGIQUES DOIVENT ÊTRE IDENTIQUES !")
print()

print("🔧 SOLUTIONS À IMPLÉMENTER:")
print("=" * 30)
print("1. Fixer calculate_completeness_score() pour vérifier le contenu")
print("2. Fixer save_current_project() pour être cohérent")
print("3. Ajouter debug dans compare_projects_advanced() pour voir ce qui se charge")
print("4. Unifier la logique de détection d'état")
print()

# Analyse du code actuel
print("📋 CODE ANALYSIS:")
print("=" * 15)

print("\n1. calculate_completeness_score() - LIGNE ~723:")
print("   'economic_analysis': 'economic_results' in st.session_state,")
print("   -> PROBLÈME: Ne vérifie pas si economic_results est vide")

print("\n2. save_current_project() - LIGNE ~928:")
print("   if 'economic_results' in st.session_state and st.session_state.economic_results:")
print("   -> CORRECT: Vérifie la présence ET le contenu")

print("\n3. compare_projects_advanced() - LIGNE ~509:")
print("   economic1 = {}")
print("   if os.path.exists(economic_path1):")
print("       with open(economic_path1, 'r') as f:")
print("           economic1 = json.load(f)")
print("   -> POTENTIEL PROBLÈME: Si le fichier existe mais est vide {}")

print("\n4. _show_economic_comparison() - LIGNE ~1603:")
print("   if not economic1 or not economic2:")
print("   -> PROBLÈME: {} est considéré comme falsy en Python")

print("\n🎯 DIAGNOSTIC FINAL:")
print("================")
print("Le problème principal est l'INCOHÉRENCE dans la détection d'état.")
print("- calculate_completeness_score() dit 'fait' si la clé existe")
print("- save_current_project() dit 'fait' si la clé existe ET n'est pas vide")
print("- La comparaison échoue car les fichiers sont probablement {}")
print()
print("SOLUTION: Harmoniser toutes ces vérifications pour qu'elles vérifient")
print("la présence ET le contenu non-vide.")