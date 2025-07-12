#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de Démarrage Serveur
========================

Script pour tester la fonction de démarrage du serveur OptimPV
depuis le panneau de contrôle.
"""

import sys
import os
from pathlib import Path

# Aller au répertoire racine du projet (2 niveaux au-dessus)
script_dir = Path(__file__).parent.parent.parent
os.chdir(script_dir)

# Ajouter le répertoire racine au path pour importer le module
sys.path.insert(0, str(script_dir))

# Importer depuis le nouveau chemin
sys.path.insert(0, str(script_dir / "server_control" / "core"))
from server_control_panel import OptimPVServerManager
import time

def test_demarrage():
    """Test de la méthode de démarrage du serveur"""
    
    print("🧪 TEST DÉMARRAGE SERVEUR OPTIMPV")
    print("=" * 50)
    print(f"📂 Répertoire de travail: {script_dir}")
    
    # Créer le gestionnaire de serveur
    print("📋 Création du gestionnaire de serveur...")
    manager = OptimPVServerManager()
    
    # Vérifier l'état initial
    print(f"🔍 État initial du serveur: {'EN LIGNE' if manager.is_server_running() else 'ARRÊTÉ'}")
    print(f"📍 Configuration: {manager.config['ip']}:{manager.config['port']}")
    
    # Si le serveur tourne déjà, l'arrêter
    if manager.is_server_running():
        print("⏹️  Arrêt du serveur existant...")
        success, message = manager.stop_server()
        print(f"   {message}")
        time.sleep(2)
    
    # Tenter de démarrer le serveur
    print("\n🚀 TENTATIVE DE DÉMARRAGE...")
    print("   (Ceci simule le clic sur 'Démarrer le Serveur' dans l'interface)")
    
    success, message = manager.start_server()
    
    print(f"\n📊 RÉSULTAT:")
    print(f"   Succès: {success}")
    print(f"   Message: {message}")
    
    if success:
        print("\n✅ SUCCÈS!")
        print("   Le serveur OptimPV a été démarré avec succès")
        print(f"   URL d'accès: {manager.get_server_url()}")
        
        # Vérifier que le serveur répond bien
        time.sleep(2)
        if manager.is_server_running():
            print("   ✅ Serveur confirmé accessible")
        else:
            print("   ⚠️  Serveur lancé mais pas accessible")
        
        # Lire les logs
        print("\n📜 LOGS RÉCENTS:")
        logs = manager.get_logs(5)
        for log in logs[-3:]:  # Dernières 3 lignes
            print(f"   {log.strip()}")
            
    else:
        print("\n❌ ÉCHEC!")
        print("   Le serveur n'a pas pu être démarré")
        print("   Consultez le message d'erreur ci-dessus")
        
        # Lire les logs d'erreur
        print("\n📜 LOGS D'ERREUR:")
        logs = manager.get_logs(5)
        for log in logs[-3:]:  # Dernières 3 lignes
            print(f"   {log.strip()}")
    
    print("\n" + "=" * 50)
    return success

if __name__ == "__main__":
    try:
        success = test_demarrage()
        
        if success:
            print("🎉 Le démarrage fonctionne parfaitement !")
            print("   Vous pouvez utiliser le panneau de contrôle normalement.")
        else:
            print("⚠️  Problème détecté dans le démarrage.")
            print("   Consultez les messages d'erreur ci-dessus.")
            
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nAppuyez sur Entrée pour fermer...") 