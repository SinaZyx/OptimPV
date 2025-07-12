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
        Détecte les remboursements TVA avec 4 méthodes de détection robustes.
        
        Returns:
            tuple: (montant_remboursement, methode_utilisee)
        """
        vat_refund = 0.0
        methode_utilisee = "AUCUNE"
        
        # MÉTHODE 1: VAT_Due_Mois négatif (crédit TVA) + VAT_Payment non nul
        if 'VAT_Due_Mois' in monthly_df.columns and 'VAT_Payment' in monthly_df.columns:
            vat_due = monthly_df.loc[date_mois, 'VAT_Due_Mois']
            vat_payment = monthly_df.loc[date_mois, 'VAT_Payment']
            
            if pd.notna(vat_due) and pd.notna(vat_payment) and vat_due < 0 and vat_payment != 0:
                vat_refund = abs(vat_due)
                methode_utilisee = "Crédit TVA (VAT_Due_Mois négatif)"
        
        # MÉTHODE 2: VAT_Payment positif direct (remboursement encaissé)
        if vat_refund == 0 and 'VAT_Payment' in monthly_df.columns:
            vat_payment = monthly_df.loc[date_mois, 'VAT_Payment']
            if pd.notna(vat_payment) and vat_payment > 0:
                vat_refund = vat_payment
                methode_utilisee = "VAT_Payment positif direct"
        
        # MÉTHODE 3: Net_VAT_Flow positif
        if vat_refund == 0 and 'Net_VAT_Flow' in monthly_df.columns:
            net_vat = monthly_df.loc[date_mois, 'Net_VAT_Flow']
            if pd.notna(net_vat) and net_vat > 0:
                vat_refund = net_vat
                methode_utilisee = "Net_VAT_Flow positif"
        
        # MÉTHODE 4: VAT_Refund dédié (fallback)
        if vat_refund == 0 and 'VAT_Refund' in monthly_df.columns:
            vat_refund_col = monthly_df.loc[date_mois, 'VAT_Refund']
            if pd.notna(vat_refund_col) and vat_refund_col > 0:
                vat_refund = vat_refund_col
                methode_utilisee = "VAT_Refund dédié"
        
        return vat_refund, methode_utilisee

    def _verify_placement_coherence(self, monthly_df):
        """
        Vérifie la cohérence mathématique des placements.
        """
        # Vérifier que la somme des soldes = Total_Placements
        for idx in monthly_df.index:
            solde_tva = monthly_df.loc[idx, 'Solde_Placement_TVA_Cumul']
            solde_provision = monthly_df.loc[idx, 'Solde_Placement_Provision_Onduleur_Cumul']
            solde_autres = monthly_df.loc[idx, 'Solde_Placement_Autres_Cumul']
            total_calcule = solde_tva + solde_provision + solde_autres
            total_enregistre = monthly_df.loc[idx, 'Total_Placements']
            
            if abs(total_calcule - total_enregistre) > 0.01:
                log_tva_placement(f"ALERTE COHÉRENCE - {idx}", {
                    "total_calculé": f"{total_calcule:,.2f}€",
                    "total_enregistré": f"{total_enregistre:,.2f}€",
                    "écart": f"{abs(total_calcule - total_enregistre):,.2f}€"
                })

    def _apply_placement_logic(self, monthly_results_df, global_config, num_total_simulation_months, duree_construction_cfg):
        """
        Applique la logique complète de placement de trésorerie sur les excédents.
        
        CRITICAL: Cette méthode NE DOIT PAS modifier les revenus en mode optimisation LCOE
        pour éviter de perturber l'algorithme de recherche du prix optimal.
        
        Args:
            monthly_results_df: DataFrame avec tous les résultats mensuels
            global_config: Configuration globale avec les paramètres de placement
            num_total_simulation_months: Nombre total de mois de simulation
            duree_construction_cfg: Durée de la phase de construction en mois
            
        Modifie:
            monthly_results_df avec les nouvelles colonnes de placement
        """
        
        # 1. INITIALISATION ET VALIDATION
        # Vérifier que les paramètres requis sont présents
        required_params = [
            "placement_tresorerie_active",
            "pourcentage_tva_a_placer", 
            "taux_placement_exces_tva",
            "taux_placement_provision_onduleur"
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
        
        # 3. CRÉATION DES COLONNES NÉCESSAIRES
        colonnes_placement = [
            'Placement_Exces_TVA',                      # Nouveau placement TVA ce mois
            'Placement_Provision_Onduleur',             # Nouveau placement provision ce mois  
            'Placement_Autres_Excedents',               # Autres placements (réservé pour évolutions)
            'Solde_Placement_TVA_Cumul',               # Solde cumulé TVA (capital + intérêts)
            'Solde_Placement_Provision_Onduleur_Cumul', # Solde cumulé provision (capital + intérêts)
            'Solde_Placement_Autres_Cumul',            # Solde autres (réservé)
            'Interets_Placements_Mensuels',            # Total des intérêts générés ce mois
            'Interets_Courus_Non_Encaisses',           # Cumul des intérêts capitalisés (non encaissés)
            'Total_Placements',                         # Somme de tous les soldes de placement
            'Tresorerie_Non_Placee'                    # Trésorerie libre disponible
        ]
        
        for col in colonnes_placement:
            if col not in monthly_results_df.columns:
                monthly_results_df[col] = 0.0
        
        # 4. RÉCUPÉRATION DES PARAMÈTRES
        pct_tva_a_placer = float(global_config.get("pourcentage_tva_a_placer", 80.0))
        taux_placement_tva_annuel = float(global_config.get("taux_placement_exces_tva", 1.5))
        taux_placement_provision_annuel = float(global_config.get("taux_placement_provision_onduleur", 2.5))
        seuil_remboursement_tva = float(global_config.get("seuil_remboursement_tva", 500.0))
        
        # Conversion en taux mensuels (intérêts composés)
        taux_tva_mensuel = (1 + taux_placement_tva_annuel/100) ** (1/12) - 1
        taux_provision_mensuel = (1 + taux_placement_provision_annuel/100) ** (1/12) - 1
        
        log_tva_placement("PARAMÈTRES DE PLACEMENT", {
            "pourcentage_tva_a_placer": f"{pct_tva_a_placer}%",
            "taux_placement_tva_annuel": f"{taux_placement_tva_annuel}%",
            "taux_placement_provision_annuel": f"{taux_placement_provision_annuel}%",
            "taux_tva_mensuel": f"{taux_tva_mensuel*100:.4f}%",
            "taux_provision_mensuel": f"{taux_provision_mensuel*100:.4f}%",
            "mode_optimisation": is_optimization_mode
        })
        
        # 5. VARIABLES DE SUIVI
        solde_placement_tva = 0.0
        solde_placement_provision = 0.0
        solde_placement_autres = 0.0
        
        # 6. BOUCLE PRINCIPALE SUR CHAQUE MOIS
        for month_idx, date_mois in enumerate(monthly_results_df.index):
            
            # Phase de construction : pas de placement
            if month_idx < duree_construction_cfg:
                continue
                
            # --- A. DÉTECTION DES REMBOURSEMENTS TVA ---
            vat_refund, methode_detection = self._detect_vat_refund(monthly_results_df, date_mois, month_idx)
            
            if vat_refund > 0:
                log_tva_placement(f"MOIS {month_idx + 1} - REMBOURSEMENT TVA DÉTECTÉ", {
                    "montant_remboursement": f"{vat_refund:,.2f}€",
                    "methode_detection": methode_detection,
                    "date": date_mois.strftime('%Y-%m-%d')
                })
            
            # --- B. PLACEMENT DES EXCÉDENTS TVA ---
            montant_a_placer_tva = 0.0
            if vat_refund >= seuil_remboursement_tva:
                montant_a_placer_tva = vat_refund * (pct_tva_a_placer / 100.0)
                monthly_results_df.loc[date_mois, 'Placement_Exces_TVA'] = montant_a_placer_tva
                
                log_tva_placement(f"MOIS {month_idx + 1} - PLACEMENT TVA", {
                    "remboursement_tva": f"{vat_refund:,.2f}€",
                    "pourcentage_place": f"{pct_tva_a_placer}%",
                    "montant_place": f"{montant_a_placer_tva:,.2f}€"
                })
            
            # --- C. PLACEMENT PROVISION ONDULEUR ---
            # Récupérer le montant de provision onduleur du mois
            provision_onduleur_mois = monthly_results_df.loc[date_mois, 'OPEX_Provision_Onduleur_Mensuel'] if 'OPEX_Provision_Onduleur_Mensuel' in monthly_results_df.columns else 0.0
            
            if provision_onduleur_mois > 0:
                monthly_results_df.loc[date_mois, 'Placement_Provision_Onduleur'] = provision_onduleur_mois
                
                log_tva_placement(f"MOIS {month_idx + 1} - PLACEMENT PROVISION ONDULEUR", {
                    "montant_provision": f"{provision_onduleur_mois:,.2f}€"
                })
            
            # --- D. CALCUL DES INTÉRÊTS SUR SOLDES EXISTANTS ---
            interets_tva = 0.0
            interets_provision = 0.0
            interets_autres = 0.0
            
            if solde_placement_tva > 0:
                interets_tva = solde_placement_tva * taux_tva_mensuel
                
            if solde_placement_provision > 0:
                interets_provision = solde_placement_provision * taux_provision_mensuel
                
            interets_totaux = interets_tva + interets_provision + interets_autres
            monthly_results_df.loc[date_mois, 'Interets_Placements_Mensuels'] = interets_totaux
            
            if interets_totaux > 0:
                log_tva_placement(f"MOIS {month_idx + 1} - INTÉRÊTS CALCULÉS", {
                    "interets_tva": f"{interets_tva:,.2f}€",
                    "interets_provision": f"{interets_provision:,.2f}€",
                    "interets_totaux": f"{interets_totaux:,.2f}€",
                    "solde_tva_avant": f"{solde_placement_tva:,.2f}€",
                    "solde_provision_avant": f"{solde_placement_provision:,.2f}€"
                })
            
            # --- E. MISE À JOUR DES SOLDES (capital + intérêts + nouveaux placements) ---
            solde_placement_tva = solde_placement_tva + interets_tva + montant_a_placer_tva
            solde_placement_provision = solde_placement_provision + interets_provision + provision_onduleur_mois
            
            # Enregistrer les soldes cumulés
            monthly_results_df.loc[date_mois, 'Solde_Placement_TVA_Cumul'] = solde_placement_tva
            monthly_results_df.loc[date_mois, 'Solde_Placement_Provision_Onduleur_Cumul'] = solde_placement_provision
            monthly_results_df.loc[date_mois, 'Solde_Placement_Autres_Cumul'] = solde_placement_autres
            
            # Total des placements
            total_placements = solde_placement_tva + solde_placement_provision + solde_placement_autres
            monthly_results_df.loc[date_mois, 'Total_Placements'] = total_placements
            
            # Trésorerie non placée = Solde trésorerie fin (déjà calculé dans core_analyzer)
            monthly_results_df.loc[date_mois, 'Tresorerie_Non_Placee'] = monthly_results_df.loc[date_mois, 'Solde_Tresorerie_Fin_Mois']
            
            # --- F. CAPITALISATION PURE DES INTÉRÊTS (PAS D'AJOUT AUX REVENUS) ---
            # NOUVELLE APPROCHE : Les intérêts sont capitalisés mais ne deviennent pas des revenus mensuels
            # Ceci est plus réaliste fiscalement et comptablement
            
            if interets_totaux > 0:
                # Calculer le cumul des intérêts courus non encaissés
                interets_courus_cumul_precedent = 0.0
                if month_idx > 0:
                    prev_date = monthly_results_df.index[month_idx - 1]
                    interets_courus_cumul_precedent = monthly_results_df.loc[prev_date, 'Interets_Courus_Non_Encaisses']
                
                # Ajouter les nouveaux intérêts au cumul des intérêts courus
                nouveau_cumul_interets = interets_courus_cumul_precedent + interets_totaux
                monthly_results_df.loc[date_mois, 'Interets_Courus_Non_Encaisses'] = nouveau_cumul_interets
                
                log_tva_placement(f"MOIS {month_idx + 1} - INTÉRÊTS CAPITALISÉS (NON ENCAISSÉS)", {
                    "interets_du_mois": f"{interets_totaux:,.2f}€",
                    "cumul_interets_courus": f"{nouveau_cumul_interets:,.2f}€",
                    "approche": "Capitalisation pure - intérêts non comptés comme revenus mensuels",
                    "avantage": "Plus réaliste fiscalement et comptablement"
                })
            else:
                # Pas d'intérêts ce mois, mais on maintient le cumul précédent
                if month_idx > 0:
                    prev_date = monthly_results_df.index[month_idx - 1]
                    cumul_precedent = monthly_results_df.loc[prev_date, 'Interets_Courus_Non_Encaisses']
                    monthly_results_df.loc[date_mois, 'Interets_Courus_Non_Encaisses'] = cumul_precedent
        
        # 7. RÉSUMÉ FINAL
        total_interets = monthly_results_df['Interets_Placements_Mensuels'].sum()
        total_interets_courus = monthly_results_df['Interets_Courus_Non_Encaisses'].iloc[-1] if not monthly_results_df.empty else 0.0
        solde_final_tva = solde_placement_tva
        solde_final_provision = solde_placement_provision
        
        log_tva_placement("RÉSUMÉ FINAL DES PLACEMENTS - CAPITALISATION PURE", {
            "total_interets_calcules": f"{total_interets:,.2f}€",
            "total_interets_courus_non_encaisses": f"{total_interets_courus:,.2f}€",
            "solde_final_placement_tva": f"{solde_final_tva:,.2f}€",
            "solde_final_placement_provision": f"{solde_final_provision:,.2f}€",
            "approche": "Capitalisation pure - intérêts non ajoutés aux revenus",
            "avantage": "Plus réaliste fiscalement et comptablement",
            "mode_execution": "Optimisation LCOE" if is_optimization_mode else "Analyse normale"
        })
        
        # 8. VÉRIFICATION DE COHÉRENCE
        self._verify_placement_coherence(monthly_results_df)