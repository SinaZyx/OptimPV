#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimPV - Interface de Gestion des Licences
==========================================

Module dédié à la gestion des licences et des adresses MAC.
"""

import streamlit as st
import json
from datetime import datetime
from .utils import load_protection_module, normalize_mac_address, check_usb_access_realtime


def show_license_tab():
    """Onglet de gestion des licences avec gestion avancée des MACs"""
    
    st.header("🔐 Gestion des Licences")
    
    protection_enabled, _, LicenseManager = load_protection_module()
    
    if not protection_enabled or LicenseManager is None:
        st.info("""
        ### ℹ️ Protection Hardware Non Activée
        
        Le système de protection hardware n'est pas activé sur cette installation.
        Pour activer la protection basée sur l'adresse MAC :
        
        1. Assurez-vous que le module `hardware_protection.py` est présent
        2. Redémarrez l'application
        """)
        return
    
    try:
        license_manager = LicenseManager()
        
        # Statut actuel
        st.subheader("📋 Statut de la Licence")
        
        authorized, message = license_manager.check_license()
        machine_info = license_manager.get_machine_info()
        
        if authorized:
            st.success(f"✅ **Licence Valide** - {message}")
        else:
            st.error(f"❌ **Licence Invalide** - {message}")
        
        # Informations de la machine avec menu de gestion des MACs
        st.markdown("---")
        st.subheader("🖥️ Informations de la Machine")
        
        # Vérifier si l'utilisateur a la clé USB pour les permissions avancées
        has_usb_access = False
        check_usb_method = getattr(license_manager, 'check_usb_token', None)
        if check_usb_method:
            usb_valid, _ = check_usb_method()
            has_usb_access = usb_valid
        
        # Utiliser la fonction avec menu interactif
        show_machine_info_with_mac_management(license_manager, has_usb_access)
        
        # Actions
        st.markdown("---")
        st.subheader("⚙️ Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Enregistrer cette Machine", type="primary", key="license_register_machine"):
                success, reg_message = license_manager.register_machine()
                if success:
                    st.success(f"✅ {reg_message}")
                    st.rerun()
                else:
                    st.error(f"❌ {reg_message}")
        
        with col2:
            if st.button("🔄 Vérifier la Licence", key="license_verify"):
                st.rerun()
        
        with col3:
            if st.button("📊 Statut Détaillé", key="license_status"):
                status = license_manager.show_license_status()
                st.text_area("Statut Complet", value=status, height=300)
        
        # Aide
        st.markdown("---")
        st.subheader("💡 Aide")
        
        with st.expander("Comment fonctionne la protection ?"):
            st.markdown("""
            ### 🛡️ Système de Protection Hardware
            
            **Principe :**
            - Le logiciel génère un ID unique basé sur votre hardware (adresse MAC, etc.)
            - Seules les machines autorisées peuvent utiliser le logiciel
            - La licence est stockée localement dans un fichier `license.json`
            - **Clé USB** : Accès administrateur pour gérer les autorisations
            
            **Utilisation :**
            1. **Première utilisation :** Cliquez sur "Enregistrer cette Machine"
            2. **Déploiement :** Copiez le fichier `license.json` sur les autres machines autorisées
            3. **Administration :** Utilisez la clé USB pour gérer les autorisations
            4. **Vérification :** Le système vérifie automatiquement à chaque démarrage
            
            **Sécurité :**
            - Basé sur l'adresse MAC (identifiant hardware unique)
            - ID système généré avec hachage SHA-256
            - Protection contre la copie non autorisée
            - **Clé USB** : Contrôle d'accès administrateur
            """)
        
        with st.expander("Dépannage"):
            st.markdown("""
            ### 🔧 Résolution des Problèmes
            
            **"Machine non autorisée" :**
            - Vérifiez que le fichier `license.json` existe
            - Cliquez sur "Enregistrer cette Machine"
            - Contactez l'administrateur avec votre ID système
            
            **"Fichier de licence corrompu" :**
            - Supprimez le fichier `license.json`
            - Ré-enregistrez la machine
            
            **Changement de carte réseau :**
            - L'adresse MAC a changé
            - Ré-enregistrez la machine ou copiez la licence d'une machine autorisée
            
            **Accès administrateur :**
            - Insérez la clé USB avec le fichier `sys.dat`
            - Vérifiez que la clé est sur le lecteur G:
            - Rechargez la page
            """)
            
    except Exception as e:
        st.error(f"❌ Erreur lors de l'accès au système de licence : {str(e)}")
        
        if st.button("🔧 Diagnostics", key="license_diagnostics_button"):
            st.code(f"""
Erreur détaillée : {str(e)}
Type d'erreur : {type(e).__name__}
Module protection disponible : {protection_enabled}
            """)


def show_machine_info_with_mac_management(license_manager, has_usb_access=False):
    """Affiche les informations de la machine avec menu de gestion des MACs"""
    
    try:
        machine_info = license_manager.get_machine_info()
        hw_protection = license_manager.hw_protection
        hw_protection.load_license()
        
        # Informations de base de la machine
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.info(f"""
            **Nom de la machine:** {machine_info.get('hostname', 'Inconnu')}
            **ID Système:** `{machine_info.get('machine_id', 'Inconnu')}`
            **Plateforme:** {machine_info.get('platform', 'Inconnue')}
            """)
        
        with col2:
            # Statistiques des MACs
            total_macs = len(machine_info.get('mac_addresses', []))
            authorized_macs = len([mac for mac in machine_info.get('mac_addresses', []) 
                                 if mac in hw_protection.authorized_macs])
            
            st.metric("MACs Détectées", total_macs)
            st.metric("MACs Autorisées", f"{authorized_macs}/{total_macs}")
        
        # Section des adresses MAC avec menu de gestion
        st.markdown("#### 🌐 Adresses MAC Détectées")
        
        mac_addresses = machine_info.get('mac_addresses', [])
        
        if not mac_addresses:
            st.warning("Aucune adresse MAC détectée sur cette machine")
            return
        
        # Affichage interactif des MACs
        for i, mac in enumerate(mac_addresses):
            # Vérifier si cette MAC est autorisée
            is_authorized = mac in hw_protection.authorized_macs
            
            # Conteneur pour chaque MAC
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    # Affichage de la MAC avec statut
                    if is_authorized:
                        st.success(f"🟢 `{mac}`")
                    else:
                        st.error(f"🔴 `{mac}`")
                
                with col2:
                    # Statut textuel
                    if is_authorized:
                        st.write("✅ **Autorisée**")
                    else:
                        st.write("❌ **Non autorisée**")
                
                with col3:
                    # Actions selon les permissions
                    if has_usb_access:
                        # Administrateur avec clé USB
                        if is_authorized:
                            if st.button("🗑️ Supprimer", key=f"remove_mac_{i}", 
                                       help=f"Supprimer l'autorisation pour {mac}"):
                                if hw_protection.remove_authorization(mac):
                                    st.success(f"✅ MAC {mac} supprimée des autorisations")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la suppression")
                        else:
                            if st.button("➕ Autoriser", key=f"add_mac_{i}", 
                                       help=f"Autoriser {mac}"):
                                if mac not in hw_protection.authorized_macs:
                                    hw_protection.authorized_macs.append(mac)
                                    if hw_protection.save_license():
                                        st.success(f"✅ MAC {mac} autorisée")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur lors de la sauvegarde")
                                else:
                                    st.warning("⚠️ MAC déjà autorisée")
                    else:
                        # Utilisateur standard
                        if is_authorized:
                            st.write("🔒 *Autorisée*")
                        else:
                            st.write("🔒 *Non autorisée*")
                
                with col4:
                    # Informations supplémentaires
                    if st.button("ℹ️", key=f"info_mac_{i}", help=f"Informations sur {mac}"):
                        # Afficher des informations détaillées sur cette MAC
                        st.info(f"""
                        **Adresse MAC:** `{mac}`
                        **Format normalisé:** `{mac.upper().replace('-', ':')}`
                        **Statut:** {'Autorisée' if is_authorized else 'Non autorisée'}
                        **Type:** Interface réseau #{i+1}
                        """)
                
                # Ligne de séparation
                if i < len(mac_addresses) - 1:
                    st.markdown("---")
        
        # Actions globales
        st.markdown("---")
        st.markdown("#### ⚙️ Actions Globales")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if has_usb_access:
                # Autoriser toutes les MACs de cette machine
                unauthorized_macs = [mac for mac in mac_addresses 
                                   if mac not in hw_protection.authorized_macs]
                
                if unauthorized_macs:
                    if st.button("✅ Autoriser TOUTES les MACs", type="primary"):
                        added_count = 0
                        for mac in unauthorized_macs:
                            if mac not in hw_protection.authorized_macs:
                                hw_protection.authorized_macs.append(mac)
                                added_count += 1
                        
                        if hw_protection.save_license():
                            st.success(f"✅ {added_count} adresse(s) MAC autorisée(s)")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la sauvegarde")
                else:
                    st.success("✅ Toutes les MACs sont déjà autorisées")
            else:
                # Enregistrer cette machine (fonction standard)
                if st.button("📝 Enregistrer cette Machine", type="primary", key="machine_info_register"):
                    success, reg_message = license_manager.register_machine()
                    if success:
                        st.success(f"✅ {reg_message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {reg_message}")
        
        with col2:
            if has_usb_access:
                # Supprimer toutes les MACs de cette machine
                authorized_macs_here = [mac for mac in mac_addresses 
                                      if mac in hw_protection.authorized_macs]
                
                if authorized_macs_here:
                    if st.button("🗑️ Supprimer TOUTES les MACs", type="secondary"):
                        if st.button("⚠️ Confirmer la suppression", key="confirm_remove_all_macs"):
                            removed_count = 0
                            for mac in authorized_macs_here:
                                if hw_protection.remove_authorization(mac):
                                    removed_count += 1
                            
                            if removed_count > 0:
                                st.success(f"✅ {removed_count} adresse(s) MAC supprimée(s)")
                                st.rerun()
                else:
                    st.info("ℹ️ Aucune MAC autorisée à supprimer")
            else:
                # Vérifier la licence
                if st.button("🔄 Vérifier la Licence", key="machine_info_verify"):
                    st.rerun()
        
        with col3:
            # Diagnostic des MACs
            if st.button("🔍 Diagnostic MACs", key="machine_info_diagnostic"):
                st.markdown("##### 📊 Diagnostic des Adresses MAC")
                
                # Statistiques détaillées
                total = len(mac_addresses)
                authorized = len([mac for mac in mac_addresses if mac in hw_protection.authorized_macs])
                unauthorized = total - authorized
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total", total)
                with col_b:
                    st.metric("Autorisées", authorized, delta=f"{authorized/total*100:.0f}%" if total > 0 else "0%")
                with col_c:
                    st.metric("Non autorisées", unauthorized, delta=f"{unauthorized/total*100:.0f}%" if total > 0 else "0%")
                
                # Détails par MAC
                st.markdown("**Détails par adresse MAC :**")
                for mac in mac_addresses:
                    status = "✅ Autorisée" if mac in hw_protection.authorized_macs else "❌ Non autorisée"
                    st.write(f"- `{mac}` : {status}")
        
        # Section de gestion avancée des MACs (avec clé USB)
        if has_usb_access:
            st.markdown("---")
            st.markdown("#### 🔧 Gestion Avancée des Adresses MAC")
            
            # Onglets pour organiser les fonctionnalités
            tab_add, tab_list, tab_import = st.tabs(["➕ Ajouter MAC", "📋 Liste Complète", "📥 Import/Export"])
            
            with tab_add:
                st.markdown("##### ➕ Ajouter une Adresse MAC Manuellement")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Champ de saisie pour nouvelle MAC
                    new_mac = st.text_input(
                        "Adresse MAC à ajouter",
                        placeholder="Ex: 04:D4:C4:55:AD:45 ou 04-D4-C4-55-AD-45",
                        help="Entrez une adresse MAC au format XX:XX:XX:XX:XX:XX ou XX-XX-XX-XX-XX-XX"
                    )
                    
                    # Description optionnelle
                    mac_description = st.text_input(
                        "Description (optionnel)",
                        placeholder="Ex: PC Bureau - Salle 1",
                        help="Description pour identifier cette machine"
                    )
                
                with col2:
                    st.markdown("**Formats acceptés:**")
                    st.code("""
04:D4:C4:55:AD:45
04-D4-C4-55-AD-45
04d4c455ad45
                    """)
                
                # Bouton d'ajout
                if st.button("➕ Ajouter cette MAC", type="primary", key="add_manual_mac"):
                    if new_mac.strip():
                        # Normaliser le format de la MAC
                        normalized_mac = normalize_mac_address(new_mac.strip())
                        
                        if normalized_mac:
                            if normalized_mac not in hw_protection.authorized_macs:
                                # Ajouter la MAC avec description
                                hw_protection.authorized_macs.append(normalized_mac)
                                
                                # Sauvegarder avec description si fournie
                                if mac_description.strip():
                                    # Ajouter la description dans les métadonnées
                                    if not hasattr(hw_protection, 'mac_descriptions'):
                                        hw_protection.mac_descriptions = {}
                                    hw_protection.mac_descriptions[normalized_mac] = mac_description.strip()
                                
                                if hw_protection.save_license():
                                    st.success(f"✅ MAC {normalized_mac} ajoutée avec succès!")
                                    if mac_description.strip():
                                        st.info(f"📝 Description: {mac_description.strip()}")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la sauvegarde")
                            else:
                                st.warning(f"⚠️ MAC {normalized_mac} déjà autorisée")
                        else:
                            st.error("❌ Format d'adresse MAC invalide")
                    else:
                        st.error("❌ Veuillez entrer une adresse MAC")
            
            with tab_list:
                st.markdown("##### 📋 Toutes les Adresses MAC Autorisées")
                
                all_authorized_macs = hw_protection.authorized_macs
                
                if all_authorized_macs:
                    st.info(f"**Total: {len(all_authorized_macs)} adresse(s) MAC autorisée(s)**")
                    
                    # Filtrage et recherche
                    search_mac = st.text_input("🔍 Rechercher une MAC", placeholder="Tapez pour filtrer...")
                    
                    # Filtrer les MACs selon la recherche
                    if search_mac:
                        filtered_macs = [mac for mac in all_authorized_macs 
                                       if search_mac.lower() in mac.lower()]
                    else:
                        filtered_macs = all_authorized_macs
                    
                    # Affichage de toutes les MACs autorisées
                    for i, mac in enumerate(filtered_macs):
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                # Vérifier si c'est une MAC de cette machine
                                is_local = mac in mac_addresses
                                if is_local:
                                    st.success(f"🏠 `{mac}` *(Cette machine)*")
                                else:
                                    st.info(f"🌐 `{mac}` *(Machine externe)*")
                            
                            with col2:
                                # Description si disponible
                                description = getattr(hw_protection, 'mac_descriptions', {}).get(mac, "")
                                if description:
                                    st.write(f"📝 {description}")
                                else:
                                    st.write("*Pas de description*")
                            
                            with col3:
                                # Statut et actions
                                if is_local:
                                    st.write("✅ **Machine locale**")
                                else:
                                    st.write("🌐 **Machine externe**")
                            
                            with col4:
                                # Bouton de suppression
                                if st.button("🗑️", key=f"remove_all_mac_{i}", 
                                           help=f"Supprimer {mac}"):
                                    if hw_protection.remove_authorization(mac):
                                        # Supprimer aussi la description
                                        if hasattr(hw_protection, 'mac_descriptions') and mac in hw_protection.mac_descriptions:
                                            del hw_protection.mac_descriptions[mac]
                                            hw_protection.save_license()
                                        st.success(f"✅ MAC {mac} supprimée")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur lors de la suppression")
                            
                            # Ligne de séparation
                            if i < len(filtered_macs) - 1:
                                st.markdown("---")
                    
                    # Actions globales sur toutes les MACs
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🗑️ Supprimer TOUTES les MACs", type="secondary"):
                            if st.button("⚠️ CONFIRMER - Supprimer toutes les autorisations", 
                                       key="confirm_remove_all_authorized"):
                                hw_protection.authorized_macs.clear()
                                if hasattr(hw_protection, 'mac_descriptions'):
                                    hw_protection.mac_descriptions.clear()
                                if hw_protection.save_license():
                                    st.success("✅ Toutes les autorisations supprimées")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la sauvegarde")
                    
                    with col2:
                        # Exporter la liste
                        mac_list_text = "\n".join([
                            f"{mac} - {getattr(hw_protection, 'mac_descriptions', {}).get(mac, 'Pas de description')}"
                            for mac in all_authorized_macs
                        ])
                        st.download_button(
                            "📥 Exporter la liste",
                            data=mac_list_text,
                            file_name="macs_autorisees.txt",
                            mime="text/plain"
                        )
                else:
                    st.warning("Aucune adresse MAC autorisée")
            
            with tab_import:
                st.markdown("##### 📥 Import/Export en Lot")
                
                # Import de MACs en lot
                st.markdown("**📥 Importer des MACs en lot:**")
                
                bulk_macs = st.text_area(
                    "Adresses MAC (une par ligne)",
                    placeholder="""04:D4:C4:55:AD:45
AA:BB:CC:DD:EE:FF
12-34-56-78-90-AB""",
                    height=100,
                    help="Entrez une adresse MAC par ligne, avec ou sans description"
                )
                
                if st.button("📥 Importer ces MACs", type="primary"):
                    if bulk_macs.strip():
                        lines = bulk_macs.strip().split('\n')
                        added_count = 0
                        errors = []
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Séparer MAC et description éventuelle
                            parts = line.split(' - ', 1)
                            mac_part = parts[0].strip()
                            description_part = parts[1].strip() if len(parts) > 1 else ""
                            
                            # Normaliser la MAC
                            normalized_mac = normalize_mac_address(mac_part)
                            
                            if normalized_mac:
                                if normalized_mac not in hw_protection.authorized_macs:
                                    hw_protection.authorized_macs.append(normalized_mac)
                                    
                                    # Ajouter description si fournie
                                    if description_part:
                                        if not hasattr(hw_protection, 'mac_descriptions'):
                                            hw_protection.mac_descriptions = {}
                                        hw_protection.mac_descriptions[normalized_mac] = description_part
                                    
                                    added_count += 1
                            else:
                                errors.append(f"Format invalide: {mac_part}")
                        
                        # Sauvegarder
                        if added_count > 0:
                            if hw_protection.save_license():
                                st.success(f"✅ {added_count} adresse(s) MAC importée(s)")
                                if errors:
                                    st.warning(f"⚠️ {len(errors)} erreur(s): " + ", ".join(errors))
                                st.rerun()
                            else:
                                st.error("❌ Erreur lors de la sauvegarde")
                        else:
                            st.error("❌ Aucune MAC valide à importer")
                            if errors:
                                for error in errors:
                                    st.error(error)
                    else:
                        st.error("❌ Veuillez entrer des adresses MAC")
                
                # Export formaté
                st.markdown("---")
                st.markdown("**📤 Exporter la configuration:**")
                
                if all_authorized_macs:
                    # Format détaillé avec descriptions
                    export_data = {
                        "authorized_macs": all_authorized_macs,
                        "descriptions": getattr(hw_protection, 'mac_descriptions', {}),
                        "export_date": datetime.now().isoformat(),
                        "total_count": len(all_authorized_macs)
                    }
                    
                    export_json = json.dumps(export_data, indent=2, ensure_ascii=False)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            "📤 Exporter en JSON",
                            data=export_json,
                            file_name=f"optimpv_macs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    with col2:
                        # Format texte simple
                        simple_text = "\n".join(all_authorized_macs)
                        st.download_button(
                            "📤 Exporter en TXT",
                            data=simple_text,
                            file_name=f"optimpv_macs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )

        # Message d'aide selon les permissions
        if has_usb_access:
            st.info("""
            💡 **Avec votre clé USB administrateur, vous pouvez :**
            - ➕ Autoriser/supprimer individuellement chaque adresse MAC
            - ✅ Autoriser toutes les MACs de cette machine d'un coup
            - 🗑️ Supprimer toutes les autorisations de cette machine
            - 🔧 Ajouter manuellement des MACs d'autres machines
            - 📋 Gérer toutes les MACs autorisées (locales et externes)
            - 📥 Importer/exporter des listes de MACs en lot
            - 🔍 Diagnostiquer l'état des autorisations
            """)
        else:
            st.info("""
            💡 **Actions disponibles :**
            - 📝 Enregistrer cette machine pour l'autoriser
            - 🔄 Vérifier le statut de la licence
            - 🔍 Voir le diagnostic des adresses MAC
            
            **Pour plus d'options :** Insérez votre clé USB administrateur
            """)
            
    except Exception as e:
        st.error(f"❌ Erreur lors de l'affichage des informations machine : {str(e)}") 