# modules/analysis_engine.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import traceback
import sys 
import copy 
from scipy.optimize import minimize, brentq
import logging

# Configuration du système de logging
logger = logging.getLogger(__name__)  # Logger spécifique à ce module
if not logger.handlers:  # Éviter d'ajouter des handlers multiples
    # Configuration de base si le logger racine n'est pas configuré
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,  # Niveau par défaut (peut être changé dynamiquement)
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

try:
    import numpy_financial as npf
    NPF_IS_REAL = True
    logger.info("numpy_financial chargé avec succès.")
except ImportError:
    NPF_IS_REAL = False
    logger.warning("numpy_financial non trouvé. Fonctions secours utilisées. Précision limitée pour IRR.")
    
    def secours_npv(rate, values):
        """Fonction de secours pour numpy_financial.npv avec stabilité numérique améliorée."""
        values = np.asarray(values, dtype=float) 
        if values.size == 0:
            return 0.0
        if np.isclose(rate, -1.0):
            if values.size > 0 and np.any(values[1:]):
                 return float('-inf') if values[0] >= 0 else float('inf')
            return values[0] if values.size > 0 else 0.0
        if rate < -1.0:
            return np.nan 

        # Méthode avec stabilité numérique améliorée
        try:
            pv_sum = 0.0
            log1p_rate = np.log1p(rate)  # log(1+rate), plus précis pour rate proche de 0
            
            for i, value in enumerate(values):
                if value == 0: 
                    continue
                try:
                    # Calcul avec exp(-i * log(1+rate)) au lieu de 1/(1+rate)^i
                    # pour éviter l'overflow/underflow sur les flux longs
                    log_discount_factor = -i * log1p_rate
                    if log_discount_factor > 709:  # log(sys.float_info.max) ~= 709
                        pv = 0.0  # Le facteur d'actualisation serait tellement grand que pv ~= 0
                    elif log_discount_factor < -709:
                        # Le facteur serait tellement petit (proche de 0) que pv tendrait vers l'infini
                        # Selon le signe de value, on définit la limite
                        if abs(value) < sys.float_info.epsilon:
                            pv = 0.0
                        else:
                            return np.nan  # Indéfini (potentiellement infini)
                    else:
                        discount_factor = np.exp(log_discount_factor)
                        pv = value * discount_factor
                        
                    if not np.isfinite(pv): 
                        return np.nan
                    pv_sum += pv
                except (OverflowError, FloatingPointError): 
                    return np.nan
            return pv_sum
        except Exception:  # Fallback sur l'ancienne méthode en cas d'erreur
            pv_sum = 0.0
            for i, value in enumerate(values):
                if value == 0: continue
                try:
                    discount_factor_inv = (1 + rate) ** i
                    if abs(discount_factor_inv) < sys.float_info.epsilon: # Proche de zéro
                        return np.nan if abs(value) > sys.float_info.epsilon else 0.0
                    pv = value / discount_factor_inv
                    if not np.isfinite(pv): return np.nan
                    pv_sum += pv
                except (OverflowError, FloatingPointError): return np.nan
            return pv_sum

    def secours_irr(values, guess=0.1, tol=1e-7, max_iter=100):
        values = np.asarray(values, dtype=float)
        if values.size < 2 or np.all(np.isclose(values,0)): return np.nan # Besoin d'au moins 2 flux, et pas tous nuls
        
        f_npv_for_irr = lambda r: secours_npv(r, values)
        rate_intervals = [(-0.9999, 0.5), (0.0, 1.0), (-0.5, 0.0), (0.5, 5.0), (1.0, 100.0), (-0.9, -0.01)]
        
        for r_min, r_max in rate_intervals:
            try:
                npv_min = f_npv_for_irr(r_min)
                npv_max = f_npv_for_irr(r_max)
                if pd.notna(npv_min) and pd.notna(npv_max) and (np.sign(npv_min) * np.sign(npv_max) <= 0): # Signes opposés ou un est zéro
                    if np.isclose(npv_min, 0.0): return r_min
                    if np.isclose(npv_max, 0.0): return r_max
                    if npv_min * npv_max < 0: # Strictement opposés
                        return brentq(f_npv_for_irr, r_min, r_max, xtol=tol, rtol=tol, maxiter=max_iter)
            except (RuntimeError, ValueError): 
                continue
            except Exception: 
                continue
        # print("AVERTISSEMENT MOTEUR: Fonction secours_irr limitée, n'a pas convergé.")
        return np.nan

    class NpfModule:
        @staticmethod
        def npv(rate, values): return secours_npv(rate, values)
        @staticmethod
        def irr(values): return secours_irr(values)
    npf = NpfModule()

# --- Tax Engine Import ---
try:
    from . import tax_engine 
except ImportError:
    try:
        import tax_engine 
    except ImportError:
        logger.critical("Impossible d'importer le module tax_engine.")
        class DummyTaxEngine:
            STANDARD_TAX_RATE = 0.25
            def apply_loss_carryforward_cap(self, ebt_before_loss, loss_carryforward_balance): return ebt_before_loss, loss_carryforward_balance
            def calculate_corporate_tax_pme(self, taxable_ebt): return taxable_ebt * self.STANDARD_TAX_RATE if taxable_ebt > 0 else 0.0
            def calculate_quarterly_installment(self, previous_year_tax): return previous_year_tax / 4.0 if previous_year_tax >=3000 else 0.0
        tax_engine = DummyTaxEngine()
        logger.warning("tax_engine factice utilisé. Les calculs fiscaux seront incorrects.")

# --- TURPE Import ---
try:
    from modules.config import TURPE_PROD_RATES 
except ImportError:
    logger.error("Impossible d'importer TURPE_PROD_RATES. TURPE sera nul.")
    TURPE_PROD_RATES = {}

class AnalysisEngine:
    def __init__(self, config: dict, scenarios: dict, sites_data: dict[str, pd.DataFrame]):
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(scenarios, dict): raise TypeError("scenarios doit être un dict")
        if not isinstance(sites_data, dict): raise TypeError("sites_data doit être un dict")
        
        self.config = copy.deepcopy(config)
        self.scenarios = copy.deepcopy(scenarios)
        self.sites_data = {} # Initialiser vide, puis remplir avec validation
        
        required_cols = ['Temps', 'production_kwh', 'consumption_kwh']
        for site_id, df_site_init in sites_data.items(): # Utiliser sites_data passé en argument
            if not isinstance(df_site_init, pd.DataFrame):
                logger.warning(f"Données du site '{site_id}' non DataFrame, ignorées.")
                continue
            
            df_copy = df_site_init.copy() # Travailler sur une copie pour la validation/conversion

            if not df_copy.empty:
                if 'Temps' not in df_copy.columns:
                    raise ValueError(f"Colonne 'Temps' manquante pour le site '{site_id}'.")
                try:
                    if not pd.api.types.is_datetime64_any_dtype(df_copy['Temps']):
                        df_copy['Temps'] = pd.to_datetime(df_copy['Temps'], errors='raise')
                    # Vérifier NaT après conversion
                    if df_copy['Temps'].isnull().any():
                        raise ValueError(f"Conversion de 'Temps' en datetime a produit des NaT pour le site '{site_id}'.")
                except Exception as e_time: 
                    raise ValueError(f"Format de la colonne 'Temps' invalide pour le site '{site_id}': {e_time}")

                for col in ['production_kwh', 'consumption_kwh']:
                    if col not in df_copy.columns:
                        logger.warning(f"Colonne '{col}' manquante site '{site_id}'. Ajout avec zéros.")
                        df_copy[col] = 0.0 # Ajouter colonne avec zéros si manquante
                    try:
                        # Forcer la conversion en numérique, remplacer erreurs par NaN puis par 0
                        df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0.0)
                    except Exception as e_num: 
                        raise ValueError(f"Impossible de convertir la colonne '{col}' en numérique pour le site '{site_id}': {e_num}")
                self.sites_data[site_id] = df_copy # Stocker la version validée et copiée
            else:
                self.sites_data[site_id] = df_copy # Stocker le DataFrame vide

        self.npf_available = NPF_IS_REAL
        self.used_aggregated_config = False
    
    def calculate_wacc(self, debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct, wacc_type="after_tax") -> float | None:
        try:
            rd = float(taux_interet_dette_pct) / 100.0
            tc = float(taux_imposition_pct) / 100.0 
            re = float(cout_fonds_propres_pct) / 100.0
            dr = float(debt_ratio)

            if not (0 <= dr <= 1): raise ValueError("Debt ratio doit être entre 0 et 1")
            if not (0 <= tc < 1): raise ValueError("Taux imposition (pour bouclier fiscal dette) doit être entre 0 et 100[")
            if rd < 0 or re < 0: raise ValueError("Taux d'intérêt ou coût fonds propres négatifs invalides")

            equity_ratio = 1.0 - dr
            cout_dette_apres_impots = rd * (1.0 - tc)
            wacc_at = (dr * cout_dette_apres_impots) + (equity_ratio * re)

            if not (pd.notna(wacc_at) and np.isfinite(wacc_at)): # Vérifier si wacc_at est valide avant de l'utiliser
                 logger.warning(f"WACC après-taxe non fini ou NaN ({wacc_at})")
                 return None

            if wacc_type == "pre_tax":
                if abs(1.0 - tc) < 1e-9: 
                    logger.warning("Taux d'imposition à 100%, WACC pré-taxe approximé sans effet fiscal direct.")
                    wacc_pt = (dr * rd) + (equity_ratio * re) 
                else:
                    wacc_pt = wacc_at / (1.0 - tc)
                
                if not (pd.notna(wacc_pt) and np.isfinite(wacc_pt)): 
                    logger.warning(f"WACC pré-taxe non fini ({wacc_pt})")
                    return None
                return wacc_pt
            else: # after_tax
                return wacc_at
        except (TypeError, ValueError) as e: 
            logger.error(f"Erreur dans calculate_wacc: {e}")
            return None
        except Exception as e: 
            logger.error(f"Erreur inattendue dans calculate_wacc: {e}", exc_info=True)
            return None

    def calculate_financial_indicators(self,
                                       scenario_name: str,
                                       prix_revente: float | None = None,
                                       override_source_prix_autoconso: str | None = None,
                                       sites_config: dict | None = None) -> dict | None:
        start_time_calc = time.time()
        logger.info(f"Lancement calcul indicateurs pour '{scenario_name}'...")
        # Réinitialiser le flag à chaque appel
        self.used_aggregated_config = False 


        autoconsumption_rate = np.nan
        autoproduction_rate = np.nan
        wacc_annual_at = np.nan
        re_annual = np.nan
        lcoe = np.nan
        irr_equity = np.nan
        npv_equity = np.nan
        roi_equity = np.nan
        payback_equity_years = np.nan
        irr_project = np.nan
        npv_project = np.nan
        payback_project_years = np.nan
        avg_dscr = np.nan

        try:
            # --- 1. Récupération Config Globale et Scénario ---
            if scenario_name not in self.scenarios: raise ValueError(f"Scénario '{scenario_name}' invalide.")
            scenario = self.scenarios[scenario_name]
            global_config = self.config # Utilise la copie faite dans __init__

            # --- 2. Agrégation/Détermination des Paramètres de BASE (CAPEX, OPEX sans onduleur, Puissance) ---
            total_capex_base = 0.0
            # total_opex_base_detail_no_inverter = 0.0 # ANCIENNE LIGNE

            # NOUVELLES VARIABLES POUR OPEX DÉTAILLÉS (avant provision onduleur)
            total_opex_maintenance_base_annual = 0.0
            total_opex_assurance_base_annual = 0.0
            total_opex_admin_base_annual = 0.0
            # total_opex_autres_base_annual = 0.0 # Si vous avez une catégorie "Autres"

            total_puissance_kwc = 0.0
            total_base_annual_unindexed_inverter_provision = 0.0

            source_des_inputs = "globaux_fallback" # Par défaut si sites_config est non concluant

            effective_sites_config = sites_config if sites_config and any(sites_config.values()) else None
            
            if effective_sites_config:
                logger.debug("Utilisation de la configuration par site (sites_config) pour agrégation.")
                self.used_aggregated_config = True # Flag pour indiquer que sites_config a été utilisé
                source_des_inputs = "agreges_par_site"
                for site_id, site_cfg in effective_sites_config.items():
                    if not isinstance(site_cfg, dict): continue
                    site_power = float(site_cfg.get('puissance_kwc', 0.0))
                    site_capex = float(site_cfg.get('capex', 0.0))
                    site_type = site_cfg.get('site_type', 'Producteur')
                    
                    # site_opex_current_base_no_inv = 0.0 # ANCIENNE LIGNE
                    if site_type != "Consommateur Pur":
                        # Agrégation détaillée
                        total_opex_maintenance_base_annual += float(site_cfg.get('opex_maintenance', 0.0))
                        total_opex_assurance_base_annual += float(site_cfg.get('opex_insurance', 0.0))
                        total_opex_admin_base_annual += float(site_cfg.get('opex_admin', 0.0))
                        # total_opex_autres_base_annual += float(site_cfg.get('opex_autres', 0.0)) # Si pertinent
                    
                    total_puissance_kwc += site_power
                    total_capex_base += site_capex
                    # total_opex_base_detail_no_inverter += site_opex_current_base_no_inv # ANCIENNE LIGNE (OPEX total agrégé)

                    if site_type != "Consommateur Pur" and site_cfg.get("opex_onduleur_provision_site", False):
                        cost_unindexed = float(site_cfg.get("opex_onduleur_total_cost_site", 0.0))
                        lifetime = int(site_cfg.get("opex_onduleur_lifetime_site", 0))
                        if cost_unindexed > 0 and lifetime > 0:
                            # Ajoute la provision annuelle de ce site au total
                            total_base_annual_unindexed_inverter_provision += cost_unindexed / lifetime

                capex_base_input = total_capex_base
                puissance_kwc_global = total_puissance_kwc
                # Affichage des totaux détaillés pour vérification
                logger.debug(f"Agrégats de sites_config: CAPEX={capex_base_input:,.2f}€, P_totale={puissance_kwc_global:.2f}kWc")
                logger.debug(f"  OPEX Maint. base={total_opex_maintenance_base_annual:,.2f}€/an")
                logger.debug(f"  OPEX Assur. base={total_opex_assurance_base_annual:,.2f}€/an")
                logger.debug(f"  OPEX Admin. base={total_opex_admin_base_annual:,.2f}€/an")

                # --- AJOUT POUR ROBUSTESSE OPEX (après la boucle d'agrégation de sites_config) ---
                sum_base_opex_components_from_sites = (
                    total_opex_maintenance_base_annual +
                    total_opex_assurance_base_annual +
                    total_opex_admin_base_annual
                    # + total_opex_autres_base_annual # si vous avez une catégorie "Autres"
                )
                
                if total_puissance_kwc > 0 and \
                   abs(sum_base_opex_components_from_sites) < 1e-6 and \
                   abs(total_base_annual_unindexed_inverter_provision) < 1e-6:
                    logger.warning(f"OPEX Nuls depuis sites_config: La somme des OPEX de base (maintenance, assurance, admin) ET la provision onduleur agrégées depuis 'sites_config' sont nulles pour une puissance totale de {total_puissance_kwc:.2f} kWc. Vérifiez les valeurs et les clés ('opex_maintenance', 'opex_insurance', 'opex_admin', et la configuration de la provision onduleur) dans la configuration de chaque site producteur.")
                # --- FIN AJOUT ---

            else: # Fallback si sites_config est vide ou non fourni
                logger.debug("Utilisation de la configuration globale (config) pour les inputs principaux.")
                source_des_inputs = "globaux_directs"
                self.used_aggregated_config = False
                capex_base_input = float(global_config.get('capex_scenario', 0.0))
                
                # Définir puissance_kwc_global AVANT son utilisation
                puissance_kwc_global = float(global_config.get('puissance_kwc_installee', 0.0))
                

                default_opex_maint_fallback_val = 0.0 # Ou par ex. 2.0 * puissance_kwc_global si P > 0
                default_opex_insu_fallback_val = 0.0  # Ou par ex. 1.0 * puissance_kwc_global si P > 0
                default_opex_admin_fallback_val = 0.0 # Ou par ex. 0.5 * puissance_kwc_global si P > 0
                
                opex_maint_key = 'opex_maintenance_fallback'
                if global_config.get(opex_maint_key) is not None:
                    total_opex_maintenance_base_annual = float(global_config.get(opex_maint_key))
                elif scenario.get(opex_maint_key) is not None:
                    total_opex_maintenance_base_annual = float(scenario.get(opex_maint_key))
                else:
                    total_opex_maintenance_base_annual = default_opex_maint_fallback_val
                    if puissance_kwc_global > 0: # Avertir seulement si c'est un producteur
                        logger.warning(f"AVERTISSEMENT MOTEUR: Clé OPEX '{opex_maint_key}' non trouvée dans global_config/scenario. Utilisation d'une valeur de repli interne: {total_opex_maintenance_base_annual:.2f} €/an.")

                opex_insu_key = 'opex_insurance_fallback'
                if global_config.get(opex_insu_key) is not None:
                    total_opex_assurance_base_annual = float(global_config.get(opex_insu_key))
                elif scenario.get(opex_insu_key) is not None:
                    total_opex_assurance_base_annual = float(scenario.get(opex_insu_key))
                else:
                    total_opex_assurance_base_annual = default_opex_insu_fallback_val
                    if puissance_kwc_global > 0:
                        logger.warning(f"AVERTISSEMENT MOTEUR: Clé OPEX '{opex_insu_key}' non trouvée dans global_config/scenario. Utilisation d'une valeur de repli interne: {total_opex_assurance_base_annual:.2f} €/an.")

                opex_admin_key = 'opex_admin_fallback'
                if global_config.get(opex_admin_key) is not None:
                    total_opex_admin_base_annual = float(global_config.get(opex_admin_key))
                elif scenario.get(opex_admin_key) is not None:
                    total_opex_admin_base_annual = float(scenario.get(opex_admin_key))
                else:
                    total_opex_admin_base_annual = default_opex_admin_fallback_val
                    if puissance_kwc_global > 0:
                        logger.warning(f"AVERTISSEMENT MOTEUR: Clé OPEX '{opex_admin_key}' non trouvée dans global_config/scenario. Utilisation d'une valeur de repli interne: {total_opex_admin_base_annual:.2f} €/an.")
                # --- FIN MODIFICATION ROBUSTESSE OPEX FALLBACK ---

                # Cette ligne est désormais redondante car déplacée plus haut
                # puissance_kwc_global = float(global_config.get('puissance_kwc_installee', 0.0))
                
                # Gestion de la provision onduleur pour le fallback global
                total_base_annual_unindexed_inverter_provision = 0.0 # Réinitialiser pour le cas global
                if global_config.get("opex_onduleur_provision_globale", False): # Assurez-vous que la clé est correcte
                    cost_unindexed_global = float(global_config.get("opex_onduleur_total_cost_global", 0.0))
                    lifetime_global = int(global_config.get("opex_onduleur_lifetime_global", 0))
                    if cost_unindexed_global > 0 and lifetime_global > 0:
                        total_base_annual_unindexed_inverter_provision = cost_unindexed_global / lifetime_global # Ici, on ne somme pas car c'est global

                logger.debug(f"MOTEUR: Inputs de config globale: CAPEX={capex_base_input:,.2f}€, P_globale={puissance_kwc_global:.2f}kWc")
                logger.debug(f"  OPEX Maint. base fallback={total_opex_maintenance_base_annual:,.2f}€/an")
                logger.debug(f"  OPEX Assur. base fallback={total_opex_assurance_base_annual:,.2f}€/an")
                logger.debug(f"  OPEX Admin. base fallback={total_opex_admin_base_annual:,.2f}€/an")

            # --- Application des Modificateurs de Scénario sur CAPEX, OPEX (non-onduleur) et Subvention ---
            capex_scenario_simule = capex_base_input * (1 + float(scenario.get('capex_modifier', 0.0)))
            
            # Les modificateurs d'OPEX s'appliquent à chaque composante
            opex_maintenance_base_annual_scenario = total_opex_maintenance_base_annual * (1 + float(scenario.get('opex_sauf_onduleur_modifier', 0.0)))
            opex_assurance_base_annual_scenario = total_opex_assurance_base_annual * (1 + float(scenario.get('opex_sauf_onduleur_modifier', 0.0)))
            opex_admin_base_annual_scenario = total_opex_admin_base_annual * (1 + float(scenario.get('opex_sauf_onduleur_modifier', 0.0)))
            # opex_autres_base_annual_scenario = total_opex_autres_base_annual * (1 + float(scenario.get('opex_sauf_onduleur_modifier', 0.0))) # Si pertinent

            # Calcul de la subvention basée sur pourcentage du CAPEX (première méthode)
            subvention_capex_pct_val = float(scenario.get('subvention_capex_pourcentage', 0.0)) / 100.0
            subvention_selon_pct_capex_simule = capex_scenario_simule * subvention_capex_pct_val
            # Calcul intermédiaire, non utilisé pour les calculs finaux mais conservé pour référence
            capex_net_subvention_intermediaire = capex_scenario_simule - subvention_selon_pct_capex_simule

            # --- 3. Lecture et Conversion des Paramètres Globaux de `global_config` ---
            # NOUVEAU : Paramètre de durée de construction
            duree_construction_cfg = int(global_config.get("duree_construction", 0)) # En mois
            if duree_construction_cfg < 0:
                raise ValueError("La durée de construction ne peut pas être négative.")

            # Renommer pour plus de clarté en contexte - c'est le début des opérations
            date_debut_operations_str = global_config.get("date_debut_ppa", datetime.now().date().isoformat())
            date_debut_operations = pd.to_datetime(date_debut_operations_str)
            
            # NOUVEAU : Date de début effective de TOUTE la simulation (incluant construction)
            date_debut_simulation_effective = date_debut_operations - pd.DateOffset(months=duree_construction_cfg)
            logger.info(f"Début de la simulation (construction incluse): {date_debut_simulation_effective.strftime('%Y-%m-%d')}")

            # Renommer pour éviter l'ambiguïté
            duree_exploitation_cfg = int(global_config.get("duree_ppa", 240)) # Durée de l'exploitation en mois
            if duree_exploitation_cfg <= 0:
                raise ValueError("duree_ppa (durée d'exploitation) doit être positive.")
            
            # NOUVEAU : Nombre total de mois pour la simulation (construction + exploitation)
            num_total_simulation_months = duree_construction_cfg + duree_exploitation_cfg
            logger.info(f"Durée totale: {num_total_simulation_months} mois (Construction: {duree_construction_cfg}, Exploitation: {duree_exploitation_cfg})")
            
            degradation_rate_base = float(global_config.get("degradation_rate", 0.005)) # Doit être en décimal (ex: 0.005 pour 0.5%)
            taux_inflation_pct = float(global_config.get("taux_inflation", 2.0))
            adjusted_inflation_annual = taux_inflation_pct / 100.0
            
            oa_indexed = bool(global_config.get("tarif_oa_indexe_inflation", True))
            inflation_rate_oa_pct = float(global_config.get("taux_inflation_tarif_oa", 1.89)) # Taux spécifique OA
            inflation_rate_oa_annual = inflation_rate_oa_pct / 100.0
            
            turpe_indexed = bool(global_config.get("turpe_indexe_inflation", True)) # Indexé sur inflation générale par défaut
            
            taux_imposition_standard_pct = float(global_config.get("taux_imposition", 25.0))
            tax_rate_decimal = taux_imposition_standard_pct / 100.0
            if hasattr(tax_engine, 'STANDARD_TAX_RATE'): tax_engine.STANDARD_TAX_RATE = tax_rate_decimal

            amortissement_duree_years = int(global_config.get("amortissement_duree", 20))
            if amortissement_duree_years <=0: raise ValueError("Durée d'amortissement doit être positive.")
            
            valeur_residuelle_pct_config = float(global_config.get("valeur_residuelle_pct", 0.0)) # Ex: 0.0 ou 5.0 pour 5%
            cout_demantelement_pct_config = float(global_config.get("cout_demantelement_pct", 0.0)) # Ex: 0.0 ou 2.0 pour 2%

            cout_fonds_propres_pct_config = float(global_config.get("cout_fonds_propres", 8.0))
            loan_active = global_config.get("with_loan", True)
            debt_ratio_config = float(global_config.get("debt_ratio", 0.80)) if loan_active else 0.0
            debt_term_years_config = int(global_config.get("debt_term_years", 20)) if loan_active else 0
            taux_interet_dette_pct_config = float(global_config.get("taux_interet_dette", 4.0)) if loan_active else 0.0
            taux_interet_dette_annual = taux_interet_dette_pct_config / 100.0
            
            vat_rate_operations = float(global_config.get("taux_tva_operations_pct", 20.0)) / 100.0
            vat_rate_capex = float(global_config.get("taux_tva_capex_pct", 20.0)) / 100.0
            vat_capex_recovery_month_offset = int(global_config.get("vat_capex_recovery_delay_months", 3))

            source_prix_autoc_config = global_config.get("source_prix_autoconso", "prix_initial")
            tarif_edf_ref_config = float(global_config.get("tarif_edf_reference", 0.21))
            
            # Calcul Subvention Globale
            applicable_sub_rate = 0.0
            if puissance_kwc_global <= 3: applicable_sub_rate = float(global_config.get("subvention_rate_le3",100.0))
            elif puissance_kwc_global <= 9: applicable_sub_rate = float(global_config.get("subvention_rate_le9", 80.0))
            elif puissance_kwc_global <= 36: applicable_sub_rate = float(global_config.get("subvention_rate_le36", 190.0))
            elif puissance_kwc_global <= 100: applicable_sub_rate = float(global_config.get("subvention_rate_le100", 100.0))
            elif puissance_kwc_global <= 500: applicable_sub_rate = float(global_config.get("subvention_rate_le500",0.0))
            else: applicable_sub_rate = float(global_config.get("subvention_rate_gt100", 0.0))
            
            # Nommer clairement la méthode de calcul de subvention basée sur €/kWc
            subvention_selon_eur_kwc = applicable_sub_rate * puissance_kwc_global

            # Calcul Tarif OA base
            t_oa_le9 = float(global_config.get("tarif_oa_bracket_le9", 0.0400))
            t_oa_le100 = float(global_config.get("tarif_oa_bracket_le100", 0.0761))
            t_oa_gt100 = float(global_config.get("tarif_oa_bracket_gt100", 0.0600))
            if puissance_kwc_global <= 9: tarif_oa_base = t_oa_le9
            elif puissance_kwc_global <= 100: tarif_oa_base = t_oa_le100
            else: tarif_oa_base = t_oa_gt100
            logger.info(f"MOTEUR: Tarif OA base calculé: {tarif_oa_base:.4f} €/kWh (P_globale={puissance_kwc_global:.2f} kWc)")

            # Calcul TURPE base
            if puissance_kwc_global <= 36: actual_turpe_tension = "BT<=36kVA"
            elif puissance_kwc_global <= 250: actual_turpe_tension = "BT>36kVA"
            else: actual_turpe_tension = "HTA"
            turpe_prod_contrat = global_config.get("turpe_prod_contrat", "Unique")
            if not TURPE_PROD_RATES: logger.warning("AVERTISSEMENT MOTEUR: TURPE_PROD_RATES non chargé. TURPE sera 0."); cg_rate = 0.0; cc_rate = 0.0
            else:
                cg_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CG", {}).get(turpe_prod_contrat, 0.0)
                cc_keys = list(TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).keys())
                cc_key_default = "Linky" if "Linky" in cc_keys else (cc_keys[0] if cc_keys else None)
                cc_rate = TURPE_PROD_RATES.get(actual_turpe_tension, {}).get("CC", {}).get(cc_key_default, 0.0) if cc_key_default else 0.0
            turpe_annual_base_config = cg_rate + cc_rate
            logger.info(f"MOTEUR: TURPE base recalculé: {turpe_annual_base_config:.2f} €/an (P_globale={puissance_kwc_global:.2f} kWc, Tension={actual_turpe_tension})")

            # --- 4. Application Modificateurs Scénario ---
            capex_scenario = capex_base_input * float(scenario.get("capex_modifier", 1.0))
            # opex_scenario_base_no_inverter = opex_annual_base_input_no_inverter * float(scenario.get("opex_modifier", 1.0)) # ANCIENNE LIGNE SUPPRIMÉE
            turpe_annual_base_scenario = turpe_annual_base_config # Pas de modificateur scenario sur TURPE actuellement
            
            opex_modifier_scenario = float(scenario.get("opex_modifier", 1.0))
            opex_maintenance_scenario_annual = total_opex_maintenance_base_annual * opex_modifier_scenario
            opex_assurance_scenario_annual = total_opex_assurance_base_annual * opex_modifier_scenario
            opex_admin_scenario_annual = total_opex_admin_base_annual * opex_modifier_scenario
            # opex_autres_scenario_annual = total_opex_autres_base_annual * opex_modifier_scenario # Si pertinent


            adjusted_inflation_scenario_rate = adjusted_inflation_annual * float(scenario.get("inflation_modifier", 1.0))
            degradation_rate_scenario_effective = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0)) 
            production_modifier_scenario = float(scenario.get("production_modifier", 1.0))

            # --- 5. Déterminer Prix de Vente et Source de Valorisation Autoconso ---
            prix_vente_final_a_utiliser = float(prix_revente) if prix_revente is not None else \
                                    float(global_config.get("prix_vente_initial_slider_fallback", 0.15)) # Fallback
            source_prix_autoc_effective = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config
            
            # --- 6. Agrégation Données Énergétiques ---
            if not self.sites_data or not any(not df.empty for df in self.sites_data.values()):
                # Créer un DataFrame vide avec les colonnes nécessaires si aucune donnée de site
                logger.warning("AVERTISSEMENT MOTEUR: Aucune donnée de site énergétique. Simulation avec production/consommation nulles.")
                empty_hourly_index = pd.date_range(start=date_debut_operations, periods=num_total_simulation_months * 30 * 24, freq='H') # Approximation grossière
                data_agg = pd.DataFrame(0.0, index=empty_hourly_index, columns=['production_kwh', 'consumption_kwh'])
                data_agg = data_agg.reset_index().rename(columns={'index': 'Temps'})
            else:
                # (Votre logique d'agrégation améliorée de la réponse précédente va ici)
                all_dfs = [df for df in self.sites_data.values() if not df.empty]
                min_date_list = [df['Temps'].min() for df in all_dfs]
                max_date_list = [df['Temps'].max() for df in all_dfs]
                if not min_date_list or not max_date_list: raise ValueError("Impossible de déterminer les dates min/max des données de site valides.")
                min_date = min(min_date_list)
                max_date = max(max_date_list)
                
                freq = 'H' 
                first_df_non_empty_for_freq = all_dfs[0]
                temp_times = pd.to_datetime(first_df_non_empty_for_freq['Temps'], errors='coerce').dropna().sort_values()

                if not temp_times.empty:
                    inferred_freq = pd.infer_freq(temp_times)
                    if inferred_freq: freq = inferred_freq
                    else: 
                        time_diffs = temp_times.diff().dropna()
                        if not time_diffs.empty:
                            median_diff = time_diffs.median()
                            offset_freq = pd.tseries.frequencies.to_offset(median_diff)
                            if offset_freq: freq = offset_freq
                
                common_index = pd.date_range(start=min_date, end=max_date, freq=freq)
                if common_index.empty and (not data_agg.empty if 'data_agg' in locals() else True) : # Si common_index est vide et data_agg n'a pas été initialisé pour 0 données
                    raise ValueError(f"Impossible de créer un common_index (freq={freq}, min={min_date}, max={max_date}). Vérifiez les données de temps des sites.")

                data_agg = pd.DataFrame(0.0, index=common_index, columns=['production_kwh', 'consumption_kwh'])
                
                for site_id, df_site_raw in self.sites_data.items():
                    if df_site_raw.empty: continue
                    
                    site_cfg_local = effective_sites_config.get(site_id, {}) if effective_sites_config else {}
                    site_type = site_cfg_local.get('site_type', 'Producteur')
                    
                    df_temp = df_site_raw.copy()
                    df_temp['Temps'] = pd.to_datetime(df_temp['Temps'])
                    df_temp = df_temp.set_index('Temps')
                    if df_temp.index.has_duplicates: df_temp = df_temp.groupby(df_temp.index).sum()
                    
                    # Assurer la présence des colonnes et mettre à 0 si consommateur pur
                    if 'consumption_kwh' not in df_temp.columns: df_temp['consumption_kwh'] = 0.0
                    if site_type == "Consommateur Pur":
                        df_temp['production_kwh'] = 0.0
                    elif 'production_kwh' not in df_temp.columns:
                         df_temp['production_kwh'] = 0.0
                    
                    # Reindexer et additionner
                    df_temp_reindexed = df_temp[['production_kwh', 'consumption_kwh']].reindex(common_index, fill_value=0.0)
                    data_agg = data_agg.add(df_temp_reindexed, fill_value=0.0)
                
                data_agg = data_agg.reset_index().rename(columns={'index': 'Temps'})
            hourly_data_to_return = data_agg.copy() # Copie pour le retour

            # --- 7. Préparation Structure Mensuelle ---
            # MODIFIÉ : l'index mensuel couvre maintenant toute la période incluant la construction
            monthly_index = pd.date_range(start=date_debut_simulation_effective, periods=num_total_simulation_months, freq='ME')
            monthly_results_df = pd.DataFrame(index=monthly_index)
            
            # Colonnes pour le modèle financier complet (construction + exploitation)
            monthly_cols = [
                'Is_Construction_Phase',        # NOUVEAU: 1 si construction, 0 sinon
                'Year_Index', 'Sim_Year', 'Inflation_Factor', 'Degradation_Factor',
                'Year_Index_Operational',       # NOUVEAU: Année d'exploitation 0-indexée
                'Sim_Year_Operational',         # NOUVEAU: Année d'exploitation 1-indexée
                'Inflation_Factor_Operational', # NOUVEAU: Facteur basé sur l'année opérationnelle
                'Degradation_Factor_Operational',# NOUVEAU: Facteur basé sur l'année opérationnelle
                'Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh',
                'Tarif_OA_Annuel', 'Prix_Autoconso_Annuel',
                'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total',
                'OPEX_Maintenance_Mensuel', 'OPEX_Assurance_Mensuel', 'OPEX_Admin_Mensuel',
                'OPEX_Provision_Onduleur_Mensuel', 'OPEX', 
                'TURPE', 'Amortissement', 'EBITDA', 'EBIT',
                'Interets_Payes', 'Principal_Rembourse', 'EBT',
                'Tax_Payment', 'Solde_IS_N_1_Paye_Mois', 'Total_IS_Decaisse_Mois',
                'Resultat_Net', 'FCFE', 'OCF_Projet',
                'Solde_Dette_Fin_Mois', 'Service_Dette',
                'VAT_Collectee', 'VAT_Deductible_CAPEX', 'VAT_Deductible_OPEX_TURPE', 
                'VAT_Due_Mois', 'VAT_Payment',
                'BFR_Mensuel', 'Delta_BFR_Mensuel',
                'Solde_Tresorerie_Fin_Mois',
                'CAPEX_Initial_Mensuel'          # NOUVEAU: Pour contrôler quand le CAPEX est dépensé
            ]
            for col in monthly_cols: monthly_results_df[col] = 0.0


            subvention_finale_pour_calculs = subvention_selon_eur_kwc  # On utilise la subvention basée sur €/kWc
            capex_final_pour_calculs = capex_scenario  # On utilise la deuxième définition du CAPEX modifié

            # Calcul définitif du CAPEX net de subvention pour tous les calculs financiers suivants
            capex_net_subvention = max(0, capex_final_pour_calculs - subvention_finale_pour_calculs)
            
            # NOUVEAU: Calculer la distribution du CAPEX sur les mois de construction
            if duree_construction_cfg > 0:
                # Distribution uniforme du CAPEX sur la période de construction
                capex_mensuel = capex_final_pour_calculs / duree_construction_cfg
                logger.info(f"CAPEX distribué: {capex_final_pour_calculs:.2f}€ répartis sur {duree_construction_cfg} mois = {capex_mensuel:.2f}€/mois")
            else:
                # Si pas de période de construction, tout le CAPEX est au premier mois de simulation
                capex_mensuel = capex_final_pour_calculs
                logger.info(f"CAPEX non distribué: {capex_final_pour_calculs:.2f}€ placé au premier mois")
            
            debt_amount = capex_net_subvention * debt_ratio_config if loan_active else 0.0
            net_equity_investment = capex_net_subvention - debt_amount

            if loan_active and debt_amount > 1e-6:
                monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = self.calculate_monthly_loan_schedule(
                    debt_amount, taux_interet_dette_annual, debt_term_years_config, num_total_simulation_months
                )
            else:
                zeros_array = np.zeros(num_total_simulation_months)
                monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = zeros_array.copy(), zeros_array.copy(), zeros_array.copy()
            
            val_residuelle_montant = capex_net_subvention * (valeur_residuelle_pct_config / 100.0)
            base_amortissable = capex_net_subvention - val_residuelle_montant
            annual_depreciation_base = base_amortissable / amortissement_duree_years if amortissement_duree_years > 0 else 0.0
            
            # La TVA est toujours calculée sur le CAPEX brut (avant subvention)
            tva_sur_capex_initial = capex_final_pour_calculs * vat_rate_capex

            # --- Préparation données énergétiques de référence (première année des données agrégées) ---
            df_agg_for_ref = hourly_data_to_return.set_index('Temps') # Utiliser les données agrégées finales
            if df_agg_for_ref.empty: ref_year = date_debut_operations.year # Fallback si aucune donnée
            else: ref_year = df_agg_for_ref.index.year.min()
            reference_data_ts = df_agg_for_ref[df_agg_for_ref.index.year == ref_year].copy()
            if reference_data_ts.empty: logger.warning(f"AVERTISSEMENT: Pas de données de référence pour l'année {ref_year} dans les données agrégées.")

            # --- 9. Boucle Mensuelle Principale ---
            loss_carryforward_balance = 0.0
            annual_tax_calculated_prev_year = 0.0
            current_quarterly_acompte_is = 0.0
            current_year_tracker = -1 # Pour détecter changement d'année calendaire
            
            # NOUVEAU: Tracker pour année d'exploitation (utilisé pour indexation)
            current_operational_year_tracker = -1
            
            # Initialisation des variables pour l'indexation opérationnelle
            inflation_factor_op_year_current = 1.0  # Facteur d'inflation pour l'année d'exploitation courante
            degradation_factor_op_year_current = 1.0  # Facteur de dégradation pour l'année d'exploitation courante
            
            # Initialisation des valeurs annuelles pour la première année d'exploitation (sera mise à jour au besoin)
            opex_maint_indexed_annual_op = opex_maintenance_scenario_annual
            opex_assur_indexed_annual_op = opex_assurance_scenario_annual
            opex_admin_indexed_annual_op = opex_admin_scenario_annual
            inverter_prov_indexed_annual_op = total_base_annual_unindexed_inverter_provision
            turpe_indexed_annual_op = turpe_annual_base_scenario
            depreciation_annual_op = annual_depreciation_base
            oa_rate_annual_op = tarif_oa_base
            
            # Initialisation prix autoconso pour première année d'exploitation
            if source_prix_autoc_effective == 'prix_initial':
                prix_autoc_annual_op = prix_vente_final_a_utiliser
            elif source_prix_autoc_effective == 'tarif_edf':
                prix_autoc_annual_op = tarif_edf_ref_config
            elif source_prix_autoc_effective == 'tarif_oa':
                prix_autoc_annual_op = oa_rate_annual_op
            else:
                prix_autoc_annual_op = prix_vente_final_a_utiliser
            
            # Variable pour stocker le solde d'IS de l'année N-1 à payer en N
            solde_IS_N_1_annee_precedente_a_payer_en_N = 0.0
            # Mois du paiement du solde IS (par défaut 5 = Mai)
            mois_paiement_solde_is = int(global_config.get("mois_paiement_solde_is", 5))

            # --- Initialisation pour le BFR ---
            bfr_receivables_days_config = float(global_config.get("bfr_receivables_days", 30.0))
            bfr_payables_days_config = float(global_config.get("bfr_payables_days", 15.0))
            bfr_previous_month_val = 0.0 # BFR du mois précédent, initialisé à 0 pour le premier calcul de delta
            # --- Fin Initialisation BFR ---

            inflation_factor_year_current = 1.0
            degradation_factor_year_current = 1.0
            # ... existing code ...

            opex_maintenance_indexed_annual_val = opex_maintenance_scenario_annual # Initialisation pour la première année (year_idx=0)
            opex_assurance_indexed_annual_val = opex_assurance_scenario_annual
            opex_admin_indexed_annual_val = opex_admin_scenario_annual
            # opex_autres_indexed_annual_val = opex_autres_scenario_annual # Si pertinent

            opex_current_year_no_inverter_indexed_val = (
                opex_maintenance_indexed_annual_val +
                opex_assurance_indexed_annual_val +
                opex_admin_indexed_annual_val
                # + opex_autres_indexed_annual_val # Si pertinent
            )

            turpe_current_year_indexed_val = turpe_annual_base_scenario
            depreciation_current_year_val = annual_depreciation_base if 0 < amortissement_duree_years else 0.0

            current_oa_rate_annual_val = tarif_oa_base * ((1 + inflation_rate_oa_annual)**0 if oa_indexed else 1.0)


            if source_prix_autoc_effective == 'prix_initial':
                current_prix_autoc_annual_val = prix_vente_final_a_utiliser # * inflation_factor_year_current (qui est 1.0)
            elif source_prix_autoc_effective == 'tarif_edf':
                current_prix_autoc_annual_val = tarif_edf_ref_config       # * inflation_factor_year_current
            elif source_prix_autoc_effective == 'tarif_oa':
                current_prix_autoc_annual_val = current_oa_rate_annual_val # Utilise la valeur juste définie pour l'année 0
            else: # Fallback
                current_prix_autoc_annual_val = prix_vente_final_a_utiliser # * inflation_factor_year_current
            current_year_annual_indexed_inverter_provision = total_base_annual_unindexed_inverter_provision * inflation_factor_year_current # NOUVELLE LOGIQUE LISSÉE (initialisation pour an 0)

            vat_credit_carryforward = 0.0

            for month_idx in range(num_total_simulation_months):
                current_month_end_date = monthly_index[month_idx]
                year_idx = current_month_end_date.year - date_debut_simulation_effective.year
                simulation_year_num = year_idx + 1
                
                monthly_results_df.loc[current_month_end_date, 'Year_Index'] = year_idx
                monthly_results_df.loc[current_month_end_date, 'Sim_Year'] = simulation_year_num

                # NOUVEAU: Déterminer si on est en phase de construction
                is_construction_phase = month_idx < duree_construction_cfg
                monthly_results_df.loc[current_month_end_date, 'Is_Construction_Phase'] = 1.0 if is_construction_phase else 0.0
                
                # NOUVEAU: Enregistrer le CAPEX mensuel si on est en phase de construction
                if is_construction_phase:
                    monthly_results_df.loc[current_month_end_date, 'CAPEX_Initial_Mensuel'] = capex_mensuel
                
                # NOUVEAU: Indexation basée sur l'année d'EXPLOITATION
                year_idx_op = -1  # Par défaut, pas encore en exploitation
                sim_year_num_op = 0
                
                if not is_construction_phase:
                    # Calculer l'index relatif à la phase d'exploitation
                    operational_month_idx = month_idx - duree_construction_cfg
                    year_idx_op = operational_month_idx // 12  # 0-indexed
                    sim_year_num_op = year_idx_op + 1  # 1-indexed
                    
                    if year_idx_op != current_operational_year_tracker:
                        # Début d'une nouvelle année d'EXPLOITATION
                        if year_idx_op >= 0:
                            # Mettre à jour les facteurs pour cette année d'exploitation
                            inflation_factor_op_year_current = (1 + adjusted_inflation_scenario_rate) ** year_idx_op
                            degradation_factor_op_year_current = (1 - degradation_rate_scenario_effective) ** year_idx_op
                            
                            # Recalculer les valeurs annuelles indexées pour l'année d'exploitation
                            opex_maint_indexed_annual_op = opex_maintenance_scenario_annual * inflation_factor_op_year_current
                            opex_assur_indexed_annual_op = opex_assurance_scenario_annual * inflation_factor_op_year_current
                            opex_admin_indexed_annual_op = opex_admin_scenario_annual * inflation_factor_op_year_current
                            
                            inverter_prov_indexed_annual_op = total_base_annual_unindexed_inverter_provision * inflation_factor_op_year_current
                            turpe_indexed_annual_op = turpe_annual_base_scenario * (inflation_factor_op_year_current if turpe_indexed else 1.0)
                            depreciation_annual_op = annual_depreciation_base if year_idx_op < amortissement_duree_years else 0.0
                            
                            oa_rate_annual_op = tarif_oa_base * ((1 + inflation_rate_oa_annual)**year_idx_op if oa_indexed else 1.0)
                            
                            if source_prix_autoc_effective == 'prix_initial':
                                prix_autoc_annual_op = prix_vente_final_a_utiliser * inflation_factor_op_year_current
                            elif source_prix_autoc_effective == 'tarif_edf':
                                prix_autoc_annual_op = tarif_edf_ref_config * inflation_factor_op_year_current
                            elif source_prix_autoc_effective == 'tarif_oa':
                                prix_autoc_annual_op = oa_rate_annual_op
                            else:
                                prix_autoc_annual_op = prix_vente_final_a_utiliser * inflation_factor_op_year_current
                        
                        current_operational_year_tracker = year_idx_op
                
                # Enregistrer les données d'indexation opérationnelle
                monthly_results_df.loc[current_month_end_date, 'Year_Index_Operational'] = year_idx_op
                monthly_results_df.loc[current_month_end_date, 'Sim_Year_Operational'] = sim_year_num_op
                monthly_results_df.loc[current_month_end_date, 'Inflation_Factor_Operational'] = inflation_factor_op_year_current
                monthly_results_df.loc[current_month_end_date, 'Degradation_Factor_Operational'] = degradation_factor_op_year_current


                if current_month_end_date.year != current_year_tracker:
                    # ... (votre code existant pour la détection de nouvelle année calendaire)
                    current_year_tracker = current_month_end_date.year
                    # ... (mise à jour des facteurs basés sur l'année calendaire si nécessaire)

                # -------------- PHASE DE CONSTRUCTION OU EXPLOITATION --------------
                if is_construction_phase:
                    # Phase de construction : pas de revenus, pas d'OPEX opérationnels
                    monthly_results_df.loc[current_month_end_date, ['Production_kWh', 'Consommation_kWh', 
                                                                   'Autoconsommation_kWh', 'Surplus_kWh', 
                                                                   'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total',
                                                                   'OPEX_Maintenance_Mensuel', 'OPEX_Assurance_Mensuel', 
                                                                   'OPEX_Admin_Mensuel', 'OPEX_Provision_Onduleur_Mensuel', 'OPEX',
                                                                   'TURPE', 'Amortissement']] = 0.0
                else:
                    # Phase d'exploitation : calcul normal des revenus et coûts
                    # Enregistrer les tarifs annuels
                    monthly_results_df.loc[current_month_end_date, 'Tarif_OA_Annuel'] = oa_rate_annual_op
                    monthly_results_df.loc[current_month_end_date, 'Prix_Autoconso_Annuel'] = prix_autoc_annual_op
                    
                    # Calcul Énergie Mensuelle pour phase d'exploitation
                    prod_m, cons_m, auto_m, surplus_m = 0.0, 0.0, 0.0, 0.0
                    try:
                        if not reference_data_ts.empty and isinstance(reference_data_ts.index, pd.DatetimeIndex):
                            ref_monthly_energy_slice = reference_data_ts[reference_data_ts.index.month == current_month_end_date.month]
                            if not ref_monthly_energy_slice.empty:
                                prod_ref_s = pd.Series(ref_monthly_energy_slice.get('production_kwh', 0.0))
                                cons_ref_s = pd.Series(ref_monthly_energy_slice.get('consumption_kwh', 0.0))
                                
                                # Utiliser le facteur de dégradation opérationnel
                                prod_adj_s = prod_ref_s * degradation_factor_op_year_current * production_modifier_scenario
                                
                                prod_m = prod_adj_s.sum()
                                cons_m = cons_ref_s.sum()
                                auto_m = np.minimum(prod_m, cons_m)
                                surplus_m = max(0, prod_m - auto_m)
                    except Exception as e_eng_month:
                        logger.error(f"Erreur Calcul Énergie mois {current_month_end_date.month} an_op {sim_year_num_op}: {e_eng_month}")
                    
                    monthly_results_df.loc[current_month_end_date, 'Production_kWh'] = prod_m
                    monthly_results_df.loc[current_month_end_date, 'Consommation_kWh'] = cons_m
                    monthly_results_df.loc[current_month_end_date, 'Autoconsommation_kWh'] = auto_m
                    monthly_results_df.loc[current_month_end_date, 'Surplus_kWh'] = surplus_m
                    
                    # Revenus (Phase d'Exploitation)
                    rev_surplus = surplus_m * oa_rate_annual_op
                    rev_auto = auto_m * prix_autoc_annual_op
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] = rev_surplus
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation'] = rev_auto
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = rev_surplus + rev_auto

                    # OPEX Mensuels (Phase d'Exploitation)
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Maintenance_Mensuel'] = opex_maint_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Assurance_Mensuel'] = opex_assur_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Admin_Mensuel'] = opex_admin_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX_Provision_Onduleur_Mensuel'] = inverter_prov_indexed_annual_op / 12.0
                    
                    opex_total_monthly_op = (opex_maint_indexed_annual_op + opex_assur_indexed_annual_op + 
                                           opex_admin_indexed_annual_op + inverter_prov_indexed_annual_op) / 12.0
                    monthly_results_df.loc[current_month_end_date, 'OPEX'] = opex_total_monthly_op
                    
                    monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_indexed_annual_op / 12.0
                    monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_annual_op / 12.0


                ebitda_m = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] - 
                           monthly_results_df.loc[current_month_end_date, 'OPEX'] - 
                           monthly_results_df.loc[current_month_end_date, 'TURPE'])
                monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_m
                
                ebit_m = ebitda_m - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_m
                
                # Intérêts et Principal calculés pour tous les mois (y compris construction)
                interest_m = monthly_interest_paid[month_idx] if month_idx < len(monthly_interest_paid) else 0.0
                principal_m = monthly_principal_paid[month_idx] if month_idx < len(monthly_principal_paid) else 0.0
                monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] = interest_m
                monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse'] = principal_m
                
                # Calculer le Service de la Dette total (intérêts + principal)
                monthly_results_df.loc[current_month_end_date, 'Service_Dette'] = interest_m + principal_m
                
                ebt_m = ebit_m - interest_m
                monthly_results_df.loc[current_month_end_date, 'EBT'] = ebt_m
                

            amortissement_mensuel = monthly_results_df['Amortissement'].fillna(0)
            principal_rembourse_mensuel = monthly_results_df['Principal_Rembourse'].fillna(0)
            ebt_mensuel = monthly_results_df['EBT'].fillna(0)
            is_decaisse_total_mensuel = monthly_results_df['Total_IS_Decaisse_Mois'].fillna(0)
            vat_payment_mensuel = monthly_results_df['VAT_Payment'].fillna(0)
            delta_bfr_mensuel_series = monthly_results_df['Delta_BFR_Mensuel'].fillna(0)
            capex_mensuel_series = monthly_results_df['CAPEX_Initial_Mensuel'].fillna(0)
            

            # ------------------------------------------------------------
            # 2‑A  Tirages de dette synchronisés avec le CAPEX
            debt_drawn_monthly_series = pd.Series(0.0, index=monthly_results_df.index)
            equity_injected_monthly_series = pd.Series(0.0, index=monthly_results_df.index)

            if duree_construction_cfg > 0:
                capex_brut = monthly_results_df['CAPEX_Initial_Mensuel'].head(duree_construction_cfg)
                # Subvention mensuelle au prorata
                subv_mth = pd.Series(0.0, index=capex_brut.index)
                if capex_final_pour_calculs > 1e-6:
                    subv_mth = (capex_brut / capex_final_pour_calculs) * subvention_finale_pour_calculs
                capex_net = capex_brut - subv_mth

                debt_drawn_monthly_series.loc[capex_net.index] = capex_net * debt_ratio_config
                equity_injected_monthly_series.loc[capex_net.index] = capex_net * (1.0 - debt_ratio_config)
            else:
                debt_drawn_monthly_series.iloc[0] = debt_amount              # cas « flash »
                equity_injected_monthly_series.iloc[0] = net_equity_investment
            # ------------------------------------------------------------


            # 3. FCFE mensuel avec dette et equity synchronisés
            net_debt_issued_monthly_series = debt_drawn_monthly_series - principal_rembourse_mensuel
            
            # Formule FCFE: inclut l'endettement net
            monthly_results_df['FCFE'] = (ebt_mensuel - is_decaisse_total_mensuel + amortissement_mensuel - 
                                         vat_payment_mensuel - delta_bfr_mensuel_series - 
                                         capex_mensuel_series + net_debt_issued_monthly_series)
            
            # 7. Contrôles de cohérence
            try:
                debt_drawn_sum = debt_drawn_monthly_series.sum()
                equity_injected_sum = equity_injected_monthly_series.sum()
                final_debt_balance = monthly_results_df['Solde_Dette_Fin_Mois'].iloc[-1] if not monthly_results_df.empty else np.nan
                
                if abs(debt_drawn_sum - debt_amount) >= 1.0:
                    logger.warning(f"Incohérence - somme tirages dette ({debt_drawn_sum:.2f}€) ≠ dette totale ({debt_amount:.2f}€)")
                
                if abs(equity_injected_sum - net_equity_investment) >= 1.0:
                    logger.warning(f"Incohérence - somme fonds propres ({equity_injected_sum:.2f}€) ≠ equity total ({net_equity_investment:.2f}€)")
                
                if pd.notna(final_debt_balance) and final_debt_balance >= 1e-2:
                    logger.warning(f"Incohérence - solde final dette ({final_debt_balance:.2f}€) non remboursé")
            except Exception as e_check:
                logger.warning(f"Échec des contrôles de cohérence: {e_check}")
            
            # Recalcul du OCF_Projet pour inclure aussi la phase de construction (inchangé)
            ebitda_mensuel_series = monthly_results_df['EBITDA'].fillna(0)
            monthly_results_df['OCF_Projet'] = ((ebitda_mensuel_series * (1.0 - tax_rate_decimal)) + 
                                               (amortissement_mensuel * tax_rate_decimal) - 
                                               capex_mensuel_series)  # Inclure CAPEX dans OCF_Projet
                                               

            initial_cash_balance_at_true_t0 = 0.0
            

            # equity_injected_monthly_series est maintenant défini dans le bloc précédent
            # avec les tirages de dette, de manière synchronisée avec le CAPEX


            
            total_company_net_cash_flow_monthly = monthly_results_df['FCFE'].fillna(0) + equity_injected_monthly_series.fillna(0)
            
            cumulative_total_company_net_cash_flow = total_company_net_cash_flow_monthly.cumsum()
            
            monthly_results_df['Solde_Tresorerie_Fin_Mois'] = initial_cash_balance_at_true_t0 + cumulative_total_company_net_cash_flow
            logger.info("Solde Trésorerie Fin Mois (basé sur T0=0 et FCFE + Equity In) calculé.")
            
                        # --- 4. Calcul du WACC et du coût des fonds propres ---
            # Initialisation correcte du WACC et du coût des fonds propres
            re_annual = float(cout_fonds_propres_pct_config)  # Coût des fonds propres annuel en %

            # Calculer le WACC avec la fonction dédiée
            wacc_annual_at = self.calculate_wacc(
                debt_ratio=debt_ratio_config,
                taux_interet_dette_pct=taux_interet_dette_pct_config, 
                taux_imposition_pct=taux_imposition_standard_pct,
                cout_fonds_propres_pct=re_annual,
                wacc_type="after_tax"
            )

            # Vérification et fallback
            if wacc_annual_at is None or not (pd.notna(wacc_annual_at) and np.isfinite(wacc_annual_at)):
                logger.warning("WACC après impôt non calculable, utilisation d'un taux de secours (6%).")
                wacc_annual_at = 6.0  # Taux de secours en %

            # FLUX POUR ACTIONNAIRES: ajouter l'investissement initial en T0
            fcfe_monthly_array = monthly_results_df['FCFE'].fillna(0).values
            
            # MODIFIÉ : Construction des flux pour les actionnaires
            if pd.isna(net_equity_investment):
                logger.warning("net_equity_investment est NaN. VAN/TRI Equity ne pourront pas être calculés correctement.")
                # Dans ce cas, equity_cash_flows_monthly ne sera pas correctement formé pour un TRI/VAN Equity.
                equity_cash_flows_monthly = np.full(len(fcfe_monthly_array) + 1, np.nan)
            else:
                # L'investissement initial des actionnaires (négatif car sortie pour eux)
                # IMPORTANT: Inclure la TVA sur CAPEX comme sortie immédiate pour les actionnaires
                initial_equity_outflow = -net_equity_investment - tva_sur_capex_initial
                logger.info(f"Flux initial actionnaires: Equity ({net_equity_investment:.2f}€) + TVA CAPEX ({tva_sur_capex_initial:.2f}€) = {-initial_equity_outflow:.2f}€")
                equity_cash_flows_monthly = np.concatenate(([initial_equity_outflow], fcfe_monthly_array))
            
            # Flux au niveau du projet reste inchangé
            ocf_monthly_array = monthly_results_df['OCF_Projet'].fillna(0).values
            project_cash_flows_monthly = ocf_monthly_array.copy()  # Pas de flux initial T0 à ajouter
            
            # Ajout de la valeur résiduelle à la fin du projet
            val_residuelle_montant_fin = capex_net_subvention * (valeur_residuelle_pct_config / 100.0)
            cout_demantelement_montant_fin = capex_final_pour_calculs * (cout_demantelement_pct_config / 100.0)
            terminal_value_net_projet = val_residuelle_montant_fin - cout_demantelement_montant_fin
            
            if len(project_cash_flows_monthly) > 0:
                project_cash_flows_monthly[-1] += terminal_value_net_projet
                
            # --- 5. Calcul des indicateurs de rentabilité ---
            
            # Conversion des taux annuels en mensuels
            re_monthly = (1 + re_annual / 100.0) ** (1/12) - 1 if pd.notna(re_annual) and re_annual > 0 else 0.08/12
            wacc_monthly_at = (1 + wacc_annual_at / 100.0) ** (1/12) - 1 if pd.notna(wacc_annual_at) and wacc_annual_at > 0 else 0.06/12
            
            # IRR, NPV, ROI pour l'equity (actionnaires)
            try:
                irr_eq_raw = npf.irr(equity_cash_flows_monthly)
                irr_equity = (1 + irr_eq_raw)**12 - 1 if pd.notna(irr_eq_raw) and np.isfinite(irr_eq_raw) else np.nan
            except Exception as e_irr_eq:
                logger.warning(f"AVERTISSEMENT: Calcul IRR_Equity impossible: {e_irr_eq}")
                irr_equity = np.nan
                
            try:
                npv_equity = npf.npv(re_monthly, equity_cash_flows_monthly)
                npv_equity = npv_equity if pd.notna(npv_equity) and np.isfinite(npv_equity) else np.nan
            except Exception as e_npv_eq:
                logger.warning(f"AVERTISSEMENT: Calcul NPV_Equity impossible: {e_npv_eq}")
                npv_equity = np.nan
                
            # ROI = NPV / Initial Equity Investment
            roi_equity = npv_equity / abs(net_equity_investment) if pd.notna(npv_equity) and abs(net_equity_investment) > 1e-9 else np.nan
            
            # IRR, NPV pour le projet global
            try:
                irr_proj_raw = npf.irr(project_cash_flows_monthly)
                irr_project = (1 + irr_proj_raw)**12 - 1 if pd.notna(irr_proj_raw) and np.isfinite(irr_proj_raw) else np.nan
            except Exception as e_irr_proj:
                logger.warning(f"AVERTISSEMENT: Calcul IRR_Project impossible: {e_irr_proj}")
                irr_project = np.nan
                
            try:
                npv_project = npf.npv(wacc_monthly_at, project_cash_flows_monthly)
                npv_project = npv_project if pd.notna(npv_project) and np.isfinite(npv_project) else np.nan
            except Exception as e_npv_proj:
                logger.warning(f"AVERTISSEMENT: Calcul NPV_Project impossible: {e_npv_proj}")
                npv_project = np.nan
                
            # Périodes de récupération
            try:
                payback_equity_months = self.calculate_payback_months(equity_cash_flows_monthly)
                payback_equity_years = payback_equity_months / 12.0 if payback_equity_months is not None else np.nan
            except Exception as e_pay_eq:
                logger.warning(f"AVERTISSEMENT: Calcul Payback_Equity impossible: {e_pay_eq}")
                payback_equity_years = np.nan
                
            try:
                payback_project_months = self.calculate_payback_months(project_cash_flows_monthly)
                payback_project_years = payback_project_months / 12.0 if payback_project_months is not None else np.nan
            except Exception as e_pay_proj:
                logger.warning(f"AVERTISSEMENT: Calcul Payback_Project impossible: {e_pay_proj}")
                payback_project_years = np.nan
            
            # Calcul du DSCR moyen (si applicable)
            avg_dscr = self.calculate_avg_dscr_revised(monthly_results_df, tax_rate_decimal) if loan_active else np.nan
            
            # --- 6. CALCUL LCOE ---
            # Utiliser le WACC mensuel déjà calculé pour actualiser les coûts et la production
            try:
                # VÉRIFICATION: S'assurer que la production est bien en kWh (pas MWh)
                total_prod_kwh = monthly_results_df['Production_kWh'].sum()
                if total_prod_kwh > 0 and total_prod_kwh < 1000 and puissance_kwc_global > 10:
                    logger.warning(f"ATTENTION: Production totale ({total_prod_kwh:.2f} kWh) très faible pour {puissance_kwc_global:.2f} kWc. Vérifiez les unités.")
                
                # Appel à la fonction calculate_lcoe_engineering
                lcoe = self.calculate_lcoe_engineering(
                    wacc_monthly_discount_rate=wacc_monthly_at,  # Même taux WACC que pour NPV projet
                    monthly_df_results=monthly_results_df,      # Contient CAPEX_Initial_Mensuel, OPEX, TURPE, Production_kWh
                    terminal_value_net_project=terminal_value_net_projet
                )
                
                # Vérification cohérence LCOE
                if pd.notna(lcoe) and lcoe > 0.20:  # LCOE > 20 c€/kWh
                    logger.warning(f"LCOE calculé anormalement élevé: {lcoe:.4f} €/kWh. Vérifiez données production et actualisation.")
            except Exception as e_lcoe:
                logger.warning(f"AVERTISSEMENT: Calcul LCOE impossible: {e_lcoe}")
                lcoe = np.nan
            
            # Calcul taux autoconsommation et autoproduction
            total_production = monthly_results_df['Production_kWh'].sum()
            total_autoconsumption = monthly_results_df['Autoconsommation_kWh'].sum()
            total_consumption = monthly_results_df['Consommation_kWh'].sum()
            
            if total_consumption > 0:
                autoconsumption_rate = total_autoconsumption / total_consumption
            else:
                autoconsumption_rate = 0.0
                
            if total_production > 0:
                autoproduction_rate = total_autoconsumption / total_production
            else:
                autoproduction_rate = 0.0
            
            # Enrichir les résultats avec les informations de temporalité
            results = {
                "scenario": scenario_name, "prix_revente": prix_vente_final_a_utiliser,
                "source_parametres_simulation": source_des_inputs,
                "capex_base_utilise": capex_base_input,
                # "opex_base_utilise_no_inverter": opex_annual_base_input_no_inverter, # ANCIENNE CLE
                "opex_base_utilise_maintenance_annuel": total_opex_maintenance_base_annual,
                "opex_base_utilise_assurance_annuel": total_opex_assurance_base_annual,
                "opex_base_utilise_admin_annuel": total_opex_admin_base_annual,
                # "opex_base_utilise_autres_annuel": total_opex_autres_base_annual, # si pertinent
                "opex_base_utilise_total_hors_onduleur": (
                    total_opex_maintenance_base_annual +
                    total_opex_assurance_base_annual +
                    total_opex_admin_base_annual
                    # + total_opex_autres_base_annual # si pertinent
                ),
                "puissance_base_utilisee": puissance_kwc_global,
                "capex_scenario_simule_initial": capex_scenario_simule,  # Premier calcul du CAPEX modifié
                "capex_scenario_final_utilise": capex_final_pour_calculs,  # CAPEX final utilisé pour les calculs
                "capex_net_subvention_final": capex_net_subvention,  # CAPEX net final utilisé
                # Informations sur les deux méthodes de calcul de subvention
                "subvention_calculee_pct_capex": subvention_selon_pct_capex_simule,
                "subvention_calculee_eur_kwc": subvention_selon_eur_kwc,
                "subvention_finale_retenue_pour_calculs": subvention_finale_pour_calculs,
                "capex_net_subvention_intermediaire_avant_maj": capex_net_subvention_intermediaire,  # Valeur intermédiaire non utilisée
                # "opex_scenario_base_no_inverter_simule": opex_scenario_base_no_inverter, # ANCIENNE CLE
                "opex_scenario_maintenance_annuel_simule": opex_maintenance_scenario_annual,
                "opex_scenario_assurance_annuel_simule": opex_assurance_scenario_annual,
                "opex_scenario_admin_annuel_simule": opex_admin_scenario_annual,
                # "opex_scenario_autres_annuel_simule": opex_autres_scenario_annual, # si pertinent
                "opex_scenario_total_hors_onduleur_simule": (
                    opex_maintenance_scenario_annual +
                    opex_assurance_scenario_annual +
                    opex_admin_scenario_annual
                    # + opex_autres_scenario_annual # si pertinent
                ),
                "equity_amount_theorique_sur_net": capex_net_subvention * (1.0 - debt_ratio_config), 
                "debt_amount": debt_amount, 
                "total_subvention": subvention_finale_pour_calculs,  # Pour compatibilité avec le code existant
                "net_equity_investment": net_equity_investment, 
                "tva_sur_capex_initial_pour_fcfe_t0": tva_sur_capex_initial,
                "autoconsumption_rate": autoconsumption_rate, 
                "autoproduction_rate": autoproduction_rate,
                "wacc_after_tax_annual": wacc_annual_at, 
                "cost_of_equity_annual": re_annual,    
                "lcoe": lcoe, 
                "irr": irr_equity, "npv": npv_equity, "roi": roi_equity, "payback_period": payback_equity_years,
                "irr_project": irr_project, "npv_project": npv_project, "payback_project": payback_project_years,
                "avg_dscr": avg_dscr,
                "monthly_data": monthly_results_df.copy(),
                'hourly_aggregated_data': hourly_data_to_return.copy(),
                "config_globale_utilisee": copy.deepcopy(global_config), 
                "config_scenario_utilise": copy.deepcopy(scenario),
                "config_sites_utilisee": copy.deepcopy(effective_sites_config) if effective_sites_config else {"mode": "global_fallback"},
                "date_debut_simulation_effective": date_debut_simulation_effective.strftime('%Y-%m-%d'),
                "date_debut_operations": date_debut_operations.strftime('%Y-%m-%d'),
                "duree_construction_mois": duree_construction_cfg,
                "duree_exploitation_mois": duree_exploitation_cfg,
            }
            end_time_calc = time.time()
            logger.info(f"MOTEUR (Mensuel): Indicateurs calculés pour '{scenario_name}' en {end_time_calc - start_time_calc:.3f} sec. Source: {source_des_inputs}")
            # Devient:
            logger.info(f"Indicateurs calculés pour '{scenario_name}' en {end_time_calc - start_time_calc:.3f} sec. Source: {source_des_inputs}")
            return results

        except (ValueError, TypeError, RuntimeError, ImportError) as e:
            logger.error(f"ERREUR MOTEUR (calculate_financial_indicators - Mensuel): Scenario '{scenario_name}', PrixRevente: {prix_revente}, Erreur: {e}")
            traceback.print_exc()
            return {"error": str(e)} # Renvoyer un dictionnaire d'erreur
        except Exception as e_unexp: 
            logger.error(f"ERREUR MOTEUR INATTENDUE (Mensuel Calculate_financial_indicators): Scenario '{scenario_name}', PrixRevente: {prix_revente}, Erreur: {e_unexp}")
            traceback.print_exc()
            return {"error": f"Erreur inattendue: {e_unexp}"} # Renvoyer un dictionnaire d'erreur

    def calculate_lcoe_engineering(self, 
                                 wacc_monthly_discount_rate: float | None, 
                                 monthly_df_results: pd.DataFrame, 
                                 terminal_value_net_project: float):
        if wacc_monthly_discount_rate is None or not (pd.notna(wacc_monthly_discount_rate) and wacc_monthly_discount_rate > -1.0):
            logger.warning("AVERTISSEMENT LCOE Eng: Taux WACC invalide ou non fourni. LCOE sera NaN.")
            return np.nan
        try:
            # --- MODIFICATION DE LA CONSTRUCTION DES FLUX DE COÛTS ---
            
            # CAPEX mensuel (dépenses positives)
            capex_monthly_values = monthly_df_results.get('CAPEX_Initial_Mensuel', 
                                                          pd.Series(0.0, index=monthly_df_results.index)).fillna(0).values
            
            # OPEX mensuels (dépenses positives)
            opex_monthly_values = monthly_df_results.get('OPEX', 
                                                         pd.Series(0.0, index=monthly_df_results.index)).fillna(0).values
            
            # TURPE mensuel (dépenses positives)
            turpe_monthly_values = monthly_df_results.get('TURPE', 
                                                          pd.Series(0.0, index=monthly_df_results.index)).fillna(0).values

            # Somme des coûts mensuels positifs
            positive_total_monthly_costs = capex_monthly_values + opex_monthly_values + turpe_monthly_values
            
            # La valeur terminale nette réduit le coût total du cycle de vie.
            if len(positive_total_monthly_costs) > 0:
                positive_total_monthly_costs[-1] -= terminal_value_net_project
            
            # NPV des coûts (les coûts étant positifs, le NPV sera la somme actualisée des dépenses)
            npv_total_costs = npf.npv(wacc_monthly_discount_rate, positive_total_monthly_costs)
            # --- FIN DE LA MODIFICATION DE LA CONSTRUCTION DES FLUX DE COÛTS ---

            if not (pd.notna(npv_total_costs) and np.isfinite(npv_total_costs)):
                logger.warning("AVERTISSEMENT LCOE Eng: NPV des coûts non valide.")
                return np.nan

            # Production d'énergie (Production_kWh doit être 0 pendant la construction)
            prod_monthly_values = monthly_df_results.get('Production_kWh', 
                                                         pd.Series(0.0, index=monthly_df_results.index)).fillna(0).values
            
            # npf.npv traite le premier élément comme étant à t=0, donc pas besoin d'ajouter un 0 initial
            npv_total_production = npf.npv(wacc_monthly_discount_rate, prod_monthly_values)

            if not (pd.notna(npv_total_production) and np.isfinite(npv_total_production)):
                logger.warning("AVERTISSEMENT LCOE Eng: NPV de la production non valide.")
                return np.nan
            
            if abs(npv_total_production) > 1e-9: 
                calculated_lcoe = npv_total_costs / npv_total_production 
                return calculated_lcoe
            else:
                logger.warning("AVERTISSEMENT LCOE Eng: NPV de la production nulle ou quasi-nulle.")
                return np.nan
        except Exception as e:
            logger.error(f"ERREUR MOTEUR (calculate_lcoe_engineering): {e}", exc_info=True)
            return np.nan

    def calculate_avg_dscr_revised(self, monthly_df_results: pd.DataFrame, corporate_tax_rate_decimal: float):
        if monthly_df_results.empty:
            logger.warning("AVERTISSEMENT DSCR: Données mensuelles vides pour DSCR.")
            return np.nan
        try:
            df_copy = monthly_df_results.copy()
            if not isinstance(df_copy.index, pd.DatetimeIndex):
                try: df_copy.index = pd.to_datetime(df_copy.index)
                except Exception as e_idx:
                    logger.error(f"ERREUR DSCR: Index non convertible en DatetimeIndex: {e_idx}"); return np.nan
            
            # Vérifier que les colonnes nécessaires existent avant resample
            required_cols_dscr = ['EBITDA', 'Tax_Payment', 'Service_Dette']
            for col_dscr in required_cols_dscr:
                if col_dscr not in df_copy.columns:
                    logger.warning(f"ERREUR DSCR: Colonne '{col_dscr}' manquante pour agrégation.")
                    return np.nan
            
            try: # Envelopper resample dans un try-except plus spécifique
                ebitda_annual = df_copy['EBITDA'].fillna(0).resample('YE').sum()
                is_paid_annual = df_copy['Tax_Payment'].fillna(0).resample('YE').sum()
                debt_service_annual = df_copy['Service_Dette'].fillna(0).resample('YE').sum()
            except Exception as e_resample:
                logger.error(f"ERREUR DSCR: Erreur lors du resample annuel: {e_resample}")
                return np.nan

            if ebitda_annual.empty and is_paid_annual.empty and debt_service_annual.empty:
                logger.warning("AVERTISSEMENT DSCR: Aucune donnée annuelle après resampling (simulation < 1 an?).")
                return np.nan

            annual_summary = pd.DataFrame({
                'EBITDA_annuel': ebitda_annual,
                'IS_Paid_annuel': is_paid_annual,
                'Service_Dette_annuel': debt_service_annual
            }).fillna(0) # Remplir les NaN potentiels après concaténation si les séries ont des longueurs différentes
            
            if annual_summary.empty : 
                logger.warning("AVERTISSEMENT DSCR: DataFrame annuel vide.")
                return np.nan

            annual_summary['CFADS_annuel'] = annual_summary['EBITDA_annuel'] - annual_summary['IS_Paid_annuel']
            
            annual_summary['DSCR_annuel'] = np.where(
                np.abs(annual_summary['Service_Dette_annuel']) > 1e-9,
                annual_summary['CFADS_annuel'] / annual_summary['Service_Dette_annuel'],
                np.inf 
            )
            annual_summary.loc[
                (annual_summary['CFADS_annuel'] <= 1e-9) & (np.abs(annual_summary['Service_Dette_annuel']) <= 1e-9),
                'DSCR_annuel'
            ] = np.nan
            
            # Correction : utiliser .loc[] au lieu de l'indexation avec []
            dscr_for_avg = annual_summary['DSCR_annuel'].loc[annual_summary['Service_Dette_annuel'] > 1e-9] # Moyenne seulement si service dette > 0
            # Correction : utiliser .loc[] pour le filtrage avec isfinite
            dscr_finite_values = dscr_for_avg.loc[np.isfinite(dscr_for_avg)]
            
            if not dscr_finite_values.empty:
                avg_dscr = dscr_finite_values.mean()
            elif not dscr_for_avg.loc[dscr_for_avg == np.inf].empty : 
                avg_dscr = np.inf
            else: 
                avg_dscr = np.nan
            return avg_dscr
        except Exception as e:
            logger.error(f"ERREUR MOTEUR (calculate_avg_dscr_revised): {e}")
            traceback.print_exc()
            return np.nan

    def simulate_selling_price(self, 
                               scenario_name: str,
                               target_irr: float | None = None, 
                               target_npv: float | None = None, 
                               override_source_prix_autoconso: str | None = None,
                               sites_config: dict | None = None
                              ) -> dict | None:
        logger.info(f"MOTEUR (SIMULATE PRICE): Scénario='{scenario_name}', Target IRR={target_irr}, Target NPV={target_npv}")
        try:
            if target_irr is None and target_npv is None:
                raise ValueError("Spécifier soit un TRI cible (target_irr) soit une VAN cible (target_npv).")

            global_config_sim = self.config 
            
            prix_min_recherche = float(global_config_sim.get('prix_min_revente', 0.01))
            prix_max_recherche = float(global_config_sim.get('prix_max_revente', 0.50))
            if prix_min_recherche >= prix_max_recherche: 
                prix_min_recherche = 0.01; prix_max_recherche = 0.50
            
            optimal_price_found = None
            simulation_cache = {}

            def get_target_metric_value(price_candidate): # Nested function
                price_key = round(price_candidate, 8) 
                if price_key in simulation_cache:
                    cached_results = simulation_cache[price_key]
                    if cached_results is None or (isinstance(cached_results, dict) and "error" in cached_results) : return np.nan 
                    if target_irr is not None: return cached_results.get('irr_project', np.nan)
                    if target_npv is not None: return cached_results.get('npv_project', np.nan)
                    return np.nan

                results_sim = self.calculate_financial_indicators( # Call to the main method
                    scenario_name, prix_revente=price_candidate,
                    override_source_prix_autoconso=override_source_prix_autoconso,
                    sites_config=sites_config
                )
                simulation_cache[price_key] = results_sim 
                
                if results_sim is None or (isinstance(results_sim, dict) and "error" in results_sim): return np.nan
                
                if target_irr is not None: return results_sim.get('irr_project', np.nan)
                if target_npv is not None: return results_sim.get('npv_project', np.nan)
                return np.nan

            def objective_for_brentq(price_candidate): # Nested function
                actual_metric_value = get_target_metric_value(price_candidate)
                if not (pd.notna(actual_metric_value) and np.isfinite(actual_metric_value)):
                    return np.nan 
                
                target_val_brentq = target_irr if target_irr is not None else target_npv
                if target_val_brentq is None : return np.nan # Should not happen if initial check passed
                return actual_metric_value - target_val_brentq

            try:
                val_min_bound = objective_for_brentq(prix_min_recherche)
                val_max_bound = objective_for_brentq(prix_max_recherche)

                if pd.notna(val_min_bound) and pd.notna(val_max_bound) and (np.sign(val_min_bound) * np.sign(val_max_bound) <= 0): # sign check
                    logger.info(f"MOTEUR (SIMULATE PRICE): Brentq bracket OK [{val_min_bound:.4f}, {val_max_bound:.4f}]")
                    optimal_price_found = brentq(objective_for_brentq, prix_min_recherche, prix_max_recherche, xtol=1e-7, rtol=1e-7, maxiter=150)
                else: logger.warning(f"MOTEUR (SIMULATE PRICE): Brentq - no sign change or NaN (Min={val_min_bound}, Max={val_max_bound}).")
            except Exception as e_brentq: logger.error(f"MOTEUR (SIMULATE PRICE): Erreur brentq : {e_brentq}.")

            if optimal_price_found is None:
                simulation_cache.clear() 
                def objective_for_minimize(price_array): # Nested function
                    price_candidate = float(price_array[0])
                    if not (prix_min_recherche <= price_candidate <= prix_max_recherche): return 1e12 
                    actual_metric_value = get_target_metric_value(price_candidate)
                    if not (pd.notna(actual_metric_value) and np.isfinite(actual_metric_value)): return 1e10 
                    target_val_minimize = target_irr if target_irr is not None else target_npv
                    if target_val_minimize is None: return 1e11 # Should not happen
                    return (actual_metric_value - target_val_minimize)**2

                initial_guess = max(prix_min_recherche, min(prix_max_recherche, (prix_min_recherche + prix_max_recherche) / 2.0))
                
                methods_to_try = [
                    ('L-BFGS-B', {'ftol': 1e-10, 'gtol': 1e-8, 'maxiter': 200}),
                    ('Nelder-Mead', {'xatol': 1e-7, 'fatol': 1e-9, 'maxiter': 300}),
                    ('SLSQP', {'ftol': 1e-9, 'maxiter': 150}) # SLSQP peut aussi être utile pour les problèmes bornés
                ]
                best_res_minimize = None

                for method_name, options in methods_to_try:
                    logger.info(f"MOTEUR (SIMULATE PRICE): Tentative avec minimize ({method_name})...")
                    simulation_cache.clear() # Vider le cache pour chaque méthode, car elles explorent différemment
                    current_bounds = [(prix_min_recherche, prix_max_recherche)] if method_name != 'Nelder-Mead' else None # Nelder-Mead ne prend pas 'bounds' directement
                    
                    res_minimize_current = minimize(
                        objective_for_minimize, [initial_guess], method=method_name, 
                        bounds=current_bounds, options=options
                    )
                    if res_minimize_current.success and abs(res_minimize_current.fun) < 1e-7: # Seuil de succès plus strict
                        optimal_price_found = res_minimize_current.x[0]
                        logger.info(f"MOTEUR (SIMULATE PRICE): {method_name} a convergé vers {optimal_price_found:.8f} (obj={res_minimize_current.fun:.2e})")
                        break # Sortir si une bonne solution est trouvée
                    elif best_res_minimize is None or \
                         (res_minimize_current.success and 'fun' in res_minimize_current and res_minimize_current.fun < best_res_minimize.fun):
                        best_res_minimize = res_minimize_current
                        logger.info(f"MOTEUR (SIMULATE PRICE): {method_name} résultat partiel/meilleur: obj={res_minimize_current.fun:.2e}, prix={res_minimize_current.x[0]:.6f}")
                
                if optimal_price_found is None and best_res_minimize is not None and best_res_minimize.success:
                    optimal_price_found = best_res_minimize.x[0]
                    logger.warning(f"AVERTISSEMENT: Convergence stricte non atteinte, utilisation du meilleur résultat de minimize ({optimal_price_found:.6f}, obj={best_res_minimize.fun:.2e})")
            
            if optimal_price_found is None: raise RuntimeError("Aucun prix optimal déterminé après toutes les tentatives.")
            optimal_price_found = max(prix_min_recherche, min(prix_max_recherche, optimal_price_found))
            
            logger.info(f"MOTEUR (SIMULATE PRICE): Recalcul final des indicateurs avec prix optimal = {optimal_price_found:.8f}")
            simulation_cache.clear() 
            final_results_with_optimal_price = self.calculate_financial_indicators(
                scenario_name, prix_revente=optimal_price_found,
                override_source_prix_autoconso=override_source_prix_autoconso, sites_config=sites_config
            )

            if final_results_with_optimal_price and isinstance(final_results_with_optimal_price, dict) and "error" not in final_results_with_optimal_price:
                final_results_with_optimal_price['prix_revente_optimal_pour_cible'] = optimal_price_found
                final_results_with_optimal_price['target_irr_asked_for_project'] = target_irr 
                final_results_with_optimal_price['target_npv_asked_for_project'] = target_npv 
                return final_results_with_optimal_price
            else:
                error_msg = final_results_with_optimal_price.get("error", "Calcul final échoué") if isinstance(final_results_with_optimal_price, dict) else "Calcul final échoué"
                raise RuntimeError(f"Échec recalcul final avec prix {optimal_price_found:.8f}: {error_msg}")
        except Exception as e: 
            logger.error(f"ERREUR FATALE (simulate_selling_price): {e}")
            traceback.print_exc()
            return {"error": str(e)}


    def calculate_monthly_loan_schedule(self, principal, annual_rate, term_years, num_months_simulation):
        if principal < 1e-6 or term_years <= 0:
            zeros_array = np.zeros(num_months_simulation)
            return zeros_array.copy(), zeros_array.copy(), zeros_array.copy()
        
        monthly_rate = annual_rate / 12.0
        n_payments_loan_term = int(round(term_years * 12))

        monthly_payment = 0.0
        if n_payments_loan_term > 0: # Éviter division par zéro si durée nulle
            if abs(monthly_rate) < 1e-9: 
                monthly_payment = principal / n_payments_loan_term
            else:
                try:
                    factor = (1 + monthly_rate)**n_payments_loan_term
                    denominator = factor - 1
                    if abs(denominator) < 1e-12: 
                        monthly_payment = principal / n_payments_loan_term # Fallback si taux + durée -> facteur ~1
                    else:
                        monthly_payment = principal * (monthly_rate * factor) / denominator
                    if not (pd.notna(monthly_payment) and np.isfinite(monthly_payment)):
                        monthly_payment = np.nan 
                except (OverflowError, ZeroDivisionError):
                    monthly_payment = np.nan
        
        if pd.isna(monthly_payment): 
            logger.warning(f"AVERTISSEMENT ECHEANCIER: Calcul échéance impossible (P={principal}, TauxAn={annual_rate}, DuréeAn={term_years}). Prêt ignoré.")
            zeros_array = np.zeros(num_months_simulation)
            return zeros_array.copy(), zeros_array.copy(), zeros_array.copy()

        interests_paid_monthly = np.zeros(num_months_simulation)
        principals_paid_monthly = np.zeros(num_months_simulation)
        debt_balance_eom = np.zeros(num_months_simulation)
        current_balance = principal

        for i in range(num_months_simulation):
            if i < n_payments_loan_term and current_balance > 1e-6: 
                interest_for_month = current_balance * monthly_rate
                principal_payment_for_month = monthly_payment - interest_for_month
                

                principal_payment_for_month = max(0, principal_payment_for_month)
                if principal_payment_for_month > current_balance - 1e-5: # Tolérance pour le dernier paiement
                    principal_payment_for_month = current_balance 

                
                interests_paid_monthly[i] = interest_for_month
                principals_paid_monthly[i] = principal_payment_for_month
                current_balance -= principal_payment_for_month
                debt_balance_eom[i] = max(0, current_balance) 
            else: 
                interests_paid_monthly[i] = 0.0
                principals_paid_monthly[i] = 0.0
                debt_balance_eom[i] = max(0, current_balance) if i < n_payments_loan_term else 0.0 # Le solde est nul après la fin du prêt
        return interests_paid_monthly, principals_paid_monthly, debt_balance_eom

    def calculate_payback_months(self, monthly_cash_flows_with_t0: np.ndarray):
        if not isinstance(monthly_cash_flows_with_t0, np.ndarray):
            monthly_cash_flows_with_t0 = np.array(monthly_cash_flows_with_t0, dtype=float)
        
        if len(monthly_cash_flows_with_t0) < 1: return None # Nécessite au moins le flux T0
        if monthly_cash_flows_with_t0[0] >= -1e-9: return 0.0 
        if len(monthly_cash_flows_with_t0) == 1: return None # Seulement T0 négatif, pas de flux suivants

        cumulative_cf = np.cumsum(monthly_cash_flows_with_t0)
        positive_indices = np.where(cumulative_cf >= -1e-9)[0]
        
        if len(positive_indices) == 0: return None 
        first_positive_idx = positive_indices[0]
        
        if first_positive_idx == 0: return 0.0 
        
        month_before_payback_t_idx = first_positive_idx - 1 
        last_negative_cumulative_cf = cumulative_cf[month_before_payback_t_idx]
        cash_flow_of_payback_month = monthly_cash_flows_with_t0[first_positive_idx]

        if abs(cash_flow_of_payback_month) < 1e-9: 
            return float(month_before_payback_t_idx) if last_negative_cumulative_cf >= -1e-9 else None
        else:
            fraction_of_month = -last_negative_cumulative_cf / cash_flow_of_payback_month
            payback_in_months = (first_positive_idx - 1) + fraction_of_month
            
        return max(0, payback_in_months) # Assurer non-négatif, bien que T0>=0 gère le cas 0.