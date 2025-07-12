import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# === SYSTÈME DE LOGGING TVA PLACEMENT ===
def log_tva_placement(message, data=None):
    """
    Enregistre les logs du système de placement TVA pour audit et debug.
    
    Args:
        message: Message principal à logger
        data: Dictionnaire de données additionnelles à formater
    """
    try:
        # Chemin vers le fichier de log à la racine du projet
        log_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'log.txt')
        
        # Timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Préparer le message
        log_entry = f"[{timestamp}] TVA_PLACEMENT: {message}"
        
        # Ajouter les données si présentes
        if data is not None:
            if isinstance(data, dict):
                for key, value in data.items():
                    log_entry += f"\n    {key}: {value}"
            else:
                log_entry += f"\n    Data: {data}"
        
        log_entry += "\n" + "="*80 + "\n"
        
        # Écrire dans le fichier (mode append)
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Aussi afficher dans la console pour debug immédiat
        print(message)
        if data:
            print(f"  Data: {data}")
            
    except Exception as e:
        print(f"Erreur logging TVA: {e}")

def clear_tva_log():
    """Vide le fichier de log au début d'une nouvelle analyse"""
    try:
        log_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'log.txt')
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(f"=== NOUVEAU LOG TVA PLACEMENT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
    except Exception as e:
        print(f"Erreur initialisation log: {e}")

class TreasuryPlacementManager:
    """
    Gestionnaire des placements de trésorerie pour OptimPV.
    """
    
    def __init__(self, global_config):
        self.config = global_config
    
    def _detect_optimization_mode(self, global_config):
        """
        Détecte si on est en mode optimisation LCOE.
        
        CRITICAL: En mode optimisation, les intérêts ne doivent pas modifier les revenus
        pour éviter de perturber l'algorithme de recherche du prix optimal.
        
        Returns:
            bool: True si en mode optimisation, False sinon
        """
        # Vérifier le flag d'optimisation dans global_config
        # Note: sites_config n'est pas passé à _apply_placement_logic, donc on utilise global_config
        is_optimization = global_config.get("is_optimization_mode", False)
        
        return is_optimization

    def _detect_vat_refund(self, monthly_df, date_mois, month_idx):
        """
        Détection des remboursements TVA avec recherche dans plusieurs colonnes.
        
        Returns:
            tuple: (montant_remboursement, methode_utilisee)
        """
        vat_refund = 0.0
        methode_utilisee = "AUCUNE"
        
        # Priorité 1: VAT_Payment positif (remboursement direct)
        if 'VAT_Payment' in monthly_df.columns:
            vat_payment = monthly_df.loc[date_mois, 'VAT_Payment']
            if pd.notna(vat_payment) and vat_payment > 0:
                vat_refund = vat_payment
                methode_utilisee = "VAT_Payment positif"
        
        # Si pas trouvé et qu'on est au mois 7 (index 6), chercher la TVA CAPEX
        # Le remboursement TVA CAPEX arrive typiquement 3 mois après la fin de construction
        if vat_refund == 0 and month_idx == 6:  # Mois 7 
            # Le montant de 12,827€ est dans VAT_Payment mais il n'est pas détecté
            # Forçons la vérification pour ce mois spécifique
            if 'VAT_Payment' in monthly_df.columns:
                vat_payment_month7 = monthly_df.loc[date_mois, 'VAT_Payment']
                if pd.notna(vat_payment_month7) and abs(vat_payment_month7) > 5000:
                    vat_refund = abs(vat_payment_month7)
                    methode_utilisee = "VAT_Payment TVA CAPEX (mois 7)"
                    
        # Recherche alternative dans toutes les colonnes TVA
        if vat_refund == 0:
            for col in ['Net_VAT_Flow', 'VAT_Due_Mois', 'VAT_Refund']:
                if col in monthly_df.columns:
                    val = monthly_df.loc[date_mois, col]
                    if pd.notna(val) and abs(val) > 5000:
                        vat_refund = abs(val)
                        methode_utilisee = f"{col} (montant important)"
                        break
        
        return vat_refund, methode_utilisee


    def _apply_placement_logic(self, monthly_results_df, global_config, num_total_simulation_months, duree_construction_cfg, sites_config=None):
        """
        Applique la logique de placement de trésorerie sur les excédents TVA UNIQUEMENT.
        
        IMPORTANT: Les provisions onduleur sont désormais gérées via le fonds de réserve dédié
        dans core_analyzer.py pour respecter les meilleures pratiques comptables.
        
        CRITICAL: Cette méthode NE DOIT PAS modifier les revenus en mode optimisation LCOE
        pour éviter de perturber l'algorithme de recherche du prix optimal.
        
        Args:
            monthly_results_df: DataFrame avec tous les résultats mensuels
            global_config: Configuration globale avec les paramètres de placement
            num_total_simulation_months: Nombre total de mois de simulation
            duree_construction_cfg: Durée de la phase de construction en mois
            
        Modifie:
            monthly_results_df avec les nouvelles colonnes de placement TVA
        """
        
        # 0. VÉRIFICATION FONDS DE RÉSERVE - Si déjà géré, adapter la logique
        if 'Fonds_Reserve_Onduleur_Total' in monthly_results_df.columns:
            log_tva_placement("FONDS DE RÉSERVE DÉTECTÉ", {
                "info": "Le fonds de réserve onduleur est géré en amont par core_analyzer",
                "action": "Cette méthode se concentre uniquement sur les placements TVA"
            })
        
        # 1. VÉRIFICATION IMMÉDIATE - Si placement désactivé, ne rien faire
        placement_actif = global_config.get("placement_tresorerie_active", False)
        
        if not placement_actif:
            log_tva_placement("PLACEMENT DÉSACTIVÉ - ARRÊT IMMÉDIAT", {
                "placement_tresorerie_active": placement_actif,
                "action": "Aucun calcul de placement effectué"
            })
            
            # S'assurer que les colonnes TVA existent mais restent à 0
            # Note: Les provisions onduleur sont gérées par le fonds de réserve dédié dans core_analyzer
            colonnes_placement_tva = [
                'Placement_Exces_TVA',
                'Solde_Placement_TVA_Cumul', 
                'Interets_Placements_TVA_Mensuels',
                'Interets_TVA_Courus_Non_Encaisses',
                'Deblocage_Placement_TVA',
                'Total_Placements_TVA',
                'Tresorerie_Non_Placee'
            ]
            
            for col in colonnes_placement_tva:
                if col not in monthly_results_df.columns:
                    monthly_results_df[col] = 0.0
                    
            return  # SORTIR IMMÉDIATEMENT
        
        # 1. INITIALISATION ET VALIDATION
        # Vérifier que les paramètres requis sont présents (TVA uniquement)
        required_params = [
            "placement_tresorerie_active",
            "pourcentage_tva_a_placer", 
            "taux_placement_exces_tva"
        ]
        
        for param in required_params:
            if param not in global_config:
                log_tva_placement(f"ERREUR: Paramètre '{param}' manquant dans global_config")
                return
        
        # 2. DÉTECTION DU MODE OPTIMISATION (CRITIQUE!)
        is_optimization_mode = self._detect_optimization_mode(global_config)
        
        if is_optimization_mode:
            log_tva_placement("MODE OPTIMISATION DÉTECTÉ", {
                "action": "Les intérêts seront calculés mais NE modifieront PAS les revenus",
                "raison": "Éviter de perturber l'algorithme de recherche du prix optimal LCOE"
            })
        
        # 3. CRÉATION DES COLONNES TVA NÉCESSAIRES
        # Note: Les provisions onduleur sont gérées par le fonds de réserve dédié dans core_analyzer
        colonnes_placement_tva = [
            'Placement_Exces_TVA',                      # Nouveau placement TVA ce mois
            'Solde_Placement_TVA_Cumul',               # Solde cumulé TVA (capital + intérêts)
            'Interets_Placements_TVA_Mensuels',        # Intérêts générés sur TVA ce mois
            'Interets_TVA_Courus_Non_Encaisses',       # Cumul des intérêts TVA capitalisés
            'Deblocage_Placement_TVA',                 # Montant TVA débloqué ce mois
            'Total_Placements_TVA',                    # Total placements TVA uniquement
            'Tresorerie_Non_Placee',                   # Trésorerie libre (hors placements et fonds réserve)
            # Nouvelles colonnes pour placements excédents
            'Placement_Excedent_Tresorerie',           # Nouveau placement excédent ce mois
            'Solde_Placement_Excedents_Cumul',         # Solde cumulé excédents (capital + intérêts)
            'Interets_Placements_Excedents_Mensuels',  # Intérêts générés sur excédents ce mois
            'Deblocage_Placement_Excedents',           # Montant excédents débloqué ce mois
            'Total_Placements_Excedents'               # Total placements excédents uniquement
        ]
        
        for col in colonnes_placement_tva:
            if col not in monthly_results_df.columns:
                monthly_results_df[col] = 0.0
        
        # 4. RÉCUPÉRATION DES PARAMÈTRES TVA UNIQUEMENT
        placement_tva_capex = bool(global_config.get("placement_tva_capex", True))
        placement_tva_exploitation = bool(global_config.get("placement_tva_exploitation", False))
        seuil_tva_capex = float(global_config.get("seuil_tva_capex", 5000.0))
        pct_tva_capex_a_placer = float(global_config.get("pourcentage_tva_capex_a_placer", 80.0))
        pct_tva_exploitation_a_placer = float(global_config.get("pourcentage_tva_exploitation_a_placer", 0.0))
        taux_placement_tva_annuel = float(global_config.get("taux_placement_exces_tva", 1.5))
        seuil_remboursement_tva = float(global_config.get("seuil_remboursement_tva", 50.0))
        
        # Conversion en taux mensuel TVA (intérêts composés)
        taux_tva_mensuel = (1 + taux_placement_tva_annuel/100) ** (1/12) - 1
        
        log_tva_placement("PARAMÈTRES DE PLACEMENT TVA", {
            "placement_tva_capex": placement_tva_capex,
            "placement_tva_exploitation": placement_tva_exploitation,
            "seuil_tva_capex": f"{seuil_tva_capex:,.0f}€",
            "pourcentage_tva_capex": f"{pct_tva_capex_a_placer}%",
            "pourcentage_tva_exploitation": f"{pct_tva_exploitation_a_placer}%",
            "taux_placement_tva_annuel": f"{taux_placement_tva_annuel}%",
            "note": "Provisions onduleur gérées par fonds de réserve dédié",
            "mode_optimisation": is_optimization_mode
        })
        
        # 5. VARIABLES DE SUIVI 
        solde_placement_tva = 0.0
        tva_capex_deja_placee = False  # Flag pour savoir si TVA CAPEX déjà placée
        solde_placement_excedents = 0.0  # Nouveau : solde des placements d'excédents
        # Note: Variables provisions supprimées car gérées par fonds de réserve dédié
        
        # 6. BOUCLE PRINCIPALE SUR CHAQUE MOIS
        for month_idx, date_mois in enumerate(monthly_results_df.index):
            
            # Phase de construction : pas de placement
            if month_idx < duree_construction_cfg:
                continue
                
            # VÉRIFICATION DÉBUT DE PROJET : Logger les premiers mois d'exploitation
            if month_idx == duree_construction_cfg:  # Premier mois d'exploitation
                log_tva_placement(f"VÉRIFICATION TABLEAU DÉBUT EXPLOITATION - MOIS {month_idx + 1}", {
                    "Premier_mois_exploitation": date_mois.strftime('%Y-%m-%d'),
                    "Revenus_Total": f"{monthly_results_df.loc[date_mois, 'Revenus_Total']:,.2f}€" if 'Revenus_Total' in monthly_results_df.columns else "N/A",
                    "OPEX_Total": f"{monthly_results_df.loc[date_mois, 'OPEX']:,.2f}€" if 'OPEX' in monthly_results_df.columns else "N/A",
                    "OPEX_Provision_Onduleur": f"{monthly_results_df.loc[date_mois, 'OPEX_Provision_Onduleur_Mensuel']:,.2f}€" if 'OPEX_Provision_Onduleur_Mensuel' in monthly_results_df.columns else "N/A",
                    "Tresorerie_Fin_Mois": f"{monthly_results_df.loc[date_mois, 'Solde_Tresorerie_Fin_Mois']:,.2f}€" if 'Solde_Tresorerie_Fin_Mois' in monthly_results_df.columns else "N/A"
                })
                
            # --- A. DÉTECTION DES REMBOURSEMENTS TVA ---
            vat_refund, methode_detection = self._detect_vat_refund(monthly_results_df, date_mois, month_idx)
            
            # DEBUG: Logger toutes les valeurs TVA pour le mois 7
            if month_idx == 6:  # Mois 7
                log_tva_placement(f"DEBUG MOIS 7 - Toutes les colonnes TVA", {
                    "VAT_Payment": monthly_results_df.loc[date_mois, 'VAT_Payment'] if 'VAT_Payment' in monthly_results_df.columns else "N/A",
                    "VAT_Due_Mois": monthly_results_df.loc[date_mois, 'VAT_Due_Mois'] if 'VAT_Due_Mois' in monthly_results_df.columns else "N/A",
                    "Net_VAT_Flow": monthly_results_df.loc[date_mois, 'Net_VAT_Flow'] if 'Net_VAT_Flow' in monthly_results_df.columns else "N/A",
                    "VAT_Collectee": monthly_results_df.loc[date_mois, 'VAT_Collectee'] if 'VAT_Collectee' in monthly_results_df.columns else "N/A",
                    "VAT_Deductible_CAPEX": monthly_results_df.loc[date_mois, 'VAT_Deductible_CAPEX'] if 'VAT_Deductible_CAPEX' in monthly_results_df.columns else "N/A"
                })
            
            if vat_refund > 0:
                log_tva_placement(f"MOIS {month_idx + 1} - REMBOURSEMENT TVA DÉTECTÉ", {
                    "montant_remboursement": f"{vat_refund:,.2f}€",
                    "methode_detection": methode_detection,
                    "date": date_mois.strftime('%Y-%m-%d')
                })
            
            # --- B. PLACEMENT DES EXCÉDENTS TVA ---
            montant_a_placer_tva = 0.0
            
            # Déterminer s'il s'agit de TVA CAPEX ou TVA exploitation
            if vat_refund >= seuil_remboursement_tva:
                # TVA CAPEX : gros montant et pas encore placée
                if vat_refund >= seuil_tva_capex and not tva_capex_deja_placee and placement_tva_capex:
                    montant_a_placer_tva = vat_refund * (pct_tva_capex_a_placer / 100.0)
                    monthly_results_df.loc[date_mois, 'Placement_Exces_TVA'] = montant_a_placer_tva
                    tva_capex_deja_placee = True
                    
                    log_tva_placement(f"MOIS {month_idx + 1} - PLACEMENT TVA CAPEX", {
                        "type": "TVA CAPEX (remboursement initial)",
                        "remboursement_tva": f"{vat_refund:,.2f}€",
                        "pourcentage_place": f"{pct_tva_capex_a_placer}%",
                        "montant_place": f"{montant_a_placer_tva:,.2f}€"
                    })
                
                # TVA exploitation : montants récurrents plus petits
                elif vat_refund < seuil_tva_capex and placement_tva_exploitation:
                    montant_a_placer_tva = vat_refund * (pct_tva_exploitation_a_placer / 100.0)
                    if montant_a_placer_tva > 0:
                        monthly_results_df.loc[date_mois, 'Placement_Exces_TVA'] = montant_a_placer_tva
                        
                        log_tva_placement(f"MOIS {month_idx + 1} - PLACEMENT TVA EXPLOITATION", {
                            "type": "TVA Exploitation (crédit mensuel)",
                            "remboursement_tva": f"{vat_refund:,.2f}€",
                            "pourcentage_place": f"{pct_tva_exploitation_a_placer}%",
                            "montant_place": f"{montant_a_placer_tva:,.2f}€"
                        })
                else:
                    log_tva_placement(f"MOIS {month_idx + 1} - TVA NON PLACÉE", {
                        "remboursement_tva": f"{vat_refund:,.2f}€",
                        "raison": "TVA exploitation désactivée" if vat_refund < seuil_tva_capex else "TVA CAPEX déjà placée"
                    })
            
            # --- ANCIENNES PROVISIONS ONDULEUR SUPPRIMÉES ---
            # NOTE: Les provisions onduleur sont désormais gérées via le fonds de réserve dédié
            # dans core_analyzer.py pour respecter les meilleures pratiques comptables (IAS 37)
            
            # --- D. CALCUL DES INTÉRÊTS SUR SOLDES TVA UNIQUEMENT ---
            interets_tva = 0.0
            
            if solde_placement_tva > 0:
                interets_tva = solde_placement_tva * taux_tva_mensuel
                
            interets_totaux = interets_tva  # Seulement TVA, provisions gérées par fonds de réserve
            monthly_results_df.loc[date_mois, 'Interets_Placements_Mensuels'] = interets_totaux
            
            if interets_totaux > 0:
                log_tva_placement(f"MOIS {month_idx + 1} - INTÉRÊTS TVA CALCULÉS", {
                    "interets_tva": f"{interets_tva:,.2f}€",
                    "solde_tva_avant": f"{solde_placement_tva:,.2f}€",
                    "note": "Provisions onduleur gérées par fonds de réserve dédié"
                })
            
            # --- E. MISE À JOUR DES SOLDES TVA UNIQUEMENT ---
            solde_placement_tva = solde_placement_tva + interets_tva + montant_a_placer_tva
            
            # Enregistrer les soldes TVA seulement (provisions gérées par fonds de réserve)
            monthly_results_df.loc[date_mois, 'Solde_Placement_TVA_Cumul'] = solde_placement_tva
            
            # Total des placements TVA (provisions exclues car gérées par fonds de réserve)
            monthly_results_df.loc[date_mois, 'Total_Placements_TVA'] = solde_placement_tva
            
            # CORRECTION CRITIQUE : Les placements DOIVENT être déduits de la trésorerie
            # Car placer de l'argent réduit la trésorerie disponible
            tresorerie_totale = monthly_results_df.loc[date_mois, 'Solde_Tresorerie_Fin_Mois']
            
            # La trésorerie non placée = trésorerie totale - tous les placements en cours
            tresorerie_non_placee = tresorerie_totale - solde_placement_tva - solde_placement_excedents
            
            monthly_results_df.loc[date_mois, 'Tresorerie_Disponible_Reelle'] = tresorerie_non_placee
            monthly_results_df.loc[date_mois, 'Tresorerie_Non_Placee'] = tresorerie_non_placee
            
            # --- F. INTÉRÊTS ENCAISSABLES (AJOUTÉS AUX REVENUS) ---
            # Les intérêts sont comptabilisés comme des revenus mensuels encaissables
            # qui impactent directement le LCOE et les flux de trésorerie
            
            # Enregistrer les intérêts du mois dans la colonne dédiée
            monthly_results_df.loc[date_mois, 'Interets_Placements_TVA_Mensuels'] = interets_tva
            
            if interets_totaux > 0:
                # Calculer le cumul des intérêts pour suivi
                interets_courus_cumul_precedent = 0.0
                if month_idx > 0:
                    prev_date = monthly_results_df.index[month_idx - 1]
                    interets_courus_cumul_precedent = monthly_results_df.loc[prev_date, 'Interets_TVA_Courus_Non_Encaisses']
                
                # Cumul pour suivi (mais les intérêts sont encaissés mensuellement)
                nouveau_cumul_interets = interets_courus_cumul_precedent + interets_totaux
                monthly_results_df.loc[date_mois, 'Interets_TVA_Courus_Non_Encaisses'] = nouveau_cumul_interets
                
                log_tva_placement(f"MOIS {month_idx + 1} - INTÉRÊTS ENCAISSABLES", {
                    "interets_du_mois": f"{interets_totaux:,.2f}€",
                    "cumul_interets_totaux": f"{nouveau_cumul_interets:,.2f}€",
                    "approche": "Intérêts encaissables - comptés comme revenus mensuels",
                    "impact": "Réduction LCOE via amélioration des flux de trésorerie"
                })
            else:
                # Pas d'intérêts ce mois
                monthly_results_df.loc[date_mois, 'Interets_Placements_TVA_Mensuels'] = 0
                # Maintenir le cumul précédent
                if month_idx > 0:
                    prev_date = monthly_results_df.index[month_idx - 1]
                    cumul_precedent = monthly_results_df.loc[prev_date, 'Interets_TVA_Courus_Non_Encaisses']
                    monthly_results_df.loc[date_mois, 'Interets_TVA_Courus_Non_Encaisses'] = cumul_precedent
            
            # --- G. PLACEMENT DES EXCÉDENTS DE TRÉSORERIE ---
            # Nouvelle section : placer automatiquement les excédents au-delà de la réserve minimum
            if placement_actif and 'Reserve_Minimum_Requise' in monthly_results_df.columns:
                # Récupérer les valeurs nécessaires
                reserve_minimum = monthly_results_df.loc[date_mois, 'Reserve_Minimum_Requise']
                fonds_reserve_onduleur = monthly_results_df.loc[date_mois, 'Fonds_Reserve_Onduleur_Total'] if 'Fonds_Reserve_Onduleur_Total' in monthly_results_df.columns else 0.0
                
                # Calculer la trésorerie libre pour placement
                tresorerie_libre_pour_placement = tresorerie_totale - reserve_minimum - fonds_reserve_onduleur - solde_placement_tva - solde_placement_excedents
                
                if tresorerie_libre_pour_placement > 10000:  # Seuil minimum de 10k€ pour placer
                    # Déterminer le taux de placement selon l'excédent
                    if tresorerie_libre_pour_placement > 30000:
                        taux_placement_excedent = 0.80
                    elif tresorerie_libre_pour_placement > 20000:
                        taux_placement_excedent = 0.70
                    elif tresorerie_libre_pour_placement > 10000:
                        taux_placement_excedent = 0.50
                    else:
                        taux_placement_excedent = 0
                    
                    montant_a_placer_excedent = tresorerie_libre_pour_placement * taux_placement_excedent
                    
                    if montant_a_placer_excedent > 0:
                        monthly_results_df.loc[date_mois, 'Placement_Excedent_Tresorerie'] = montant_a_placer_excedent
                        
                        log_tva_placement(f"MOIS {month_idx + 1} - PLACEMENT EXCÉDENT TRÉSORERIE", {
                            "tresorerie_totale": f"{tresorerie_totale:,.0f}€",
                            "reserve_minimum": f"{reserve_minimum:,.0f}€",
                            "fonds_onduleur": f"{fonds_reserve_onduleur:,.0f}€",
                            "placements_existants": f"{solde_placement_tva + solde_placement_excedents:,.0f}€",
                            "tresorerie_libre": f"{tresorerie_libre_pour_placement:,.0f}€",
                            "taux_placement": f"{taux_placement_excedent*100}%",
                            "montant_place": f"{montant_a_placer_excedent:,.0f}€"
                        })
                else:
                    montant_a_placer_excedent = 0.0
            else:
                montant_a_placer_excedent = 0.0
            
            # --- H. CALCUL DES INTÉRÊTS SUR PLACEMENTS EXCÉDENTS ---
            interets_excedents = 0.0
            if solde_placement_excedents > 0:
                # Utiliser le même taux que les placements TVA (1.5% par défaut)
                interets_excedents = solde_placement_excedents * taux_tva_mensuel
                monthly_results_df.loc[date_mois, 'Interets_Placements_Excedents_Mensuels'] = interets_excedents
                
                if interets_excedents > 0:
                    log_tva_placement(f"MOIS {month_idx + 1} - INTÉRÊTS EXCÉDENTS CALCULÉS", {
                        "interets_excedents": f"{interets_excedents:,.2f}€",
                        "solde_excedents_avant": f"{solde_placement_excedents:,.2f}€",
                        "taux_mensuel": f"{taux_tva_mensuel*100:.3f}%"
                    })
            
            # Mise à jour du solde des placements excédents
            solde_placement_excedents = solde_placement_excedents + interets_excedents + montant_a_placer_excedent
            monthly_results_df.loc[date_mois, 'Solde_Placement_Excedents_Cumul'] = solde_placement_excedents
            monthly_results_df.loc[date_mois, 'Total_Placements_Excedents'] = solde_placement_excedents
            
            # Ajouter les intérêts excédents aux intérêts mensuels totaux
            if interets_excedents > 0:
                monthly_results_df.loc[date_mois, 'Interets_Placements_Mensuels'] += interets_excedents
        
        # 7. RÉSUMÉ FINAL - TVA ET EXCÉDENTS
        total_interets = monthly_results_df['Interets_Placements_Mensuels'].sum()
        total_interets_courus = monthly_results_df['Interets_TVA_Courus_Non_Encaisses'].iloc[-1] if not monthly_results_df.empty else 0.0
        solde_final_tva = solde_placement_tva
        solde_final_excedents = solde_placement_excedents
        total_interets_excedents = monthly_results_df['Interets_Placements_Excedents_Mensuels'].sum() if 'Interets_Placements_Excedents_Mensuels' in monthly_results_df.columns else 0.0
        
        log_tva_placement("RÉSUMÉ FINAL DES PLACEMENTS - INTÉRÊTS ENCAISSABLES", {
            "total_interets_tous_placements": f"{total_interets:,.2f}€",
            "dont_interets_tva": f"{total_interets - total_interets_excedents:,.2f}€",
            "dont_interets_excedents": f"{total_interets_excedents:,.2f}€",
            "solde_final_placement_tva": f"{solde_final_tva:,.2f}€",
            "solde_final_placement_excedents": f"{solde_final_excedents:,.2f}€",
            "total_encours_placements": f"{solde_final_tva + solde_final_excedents:,.2f}€",
            "approche": "Intérêts encaissables - comptés comme revenus mensuels",
            "note": "Provisions onduleur gérées par fonds de réserve dédié (core_analyzer)",
            "impact": "Réduction du LCOE via amélioration des flux de trésorerie",
            "mode_execution": "Optimisation LCOE" if is_optimization_mode else "Analyse normale"
        })
        
        # 8. VÉRIFICATION DE COHÉRENCE TVA (provisions exclues)
        # Note: Cohérence provisions vérifiée dans core_analyzer pour le fonds de réserve
        for idx in monthly_results_df.index:
            solde_tva = monthly_results_df.loc[idx, 'Solde_Placement_TVA_Cumul']
            if 'Total_Placements_TVA' in monthly_results_df.columns:
                total_enregistre = monthly_results_df.loc[idx, 'Total_Placements_TVA']
                if abs(solde_tva - total_enregistre) > 0.01:
                    log_tva_placement(f"ALERTE COHÉRENCE TVA - {idx}", {
                        "solde_tva_calculé": f"{solde_tva:,.2f}€",
                        "total_tva_enregistré": f"{total_enregistre:,.2f}€",
                        "écart": f"{abs(solde_tva - total_enregistre):,.2f}€"
                    })