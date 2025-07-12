# modules/analysis_engine.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta # Added timedelta for potential use
import time
import traceback
import sys
import copy
from scipy.optimize import minimize, brentq # <--- AJOUTER brentq ici
# Importer brentq SI vous voulez l'option pour NPV_equity=0 plus tard
# from scipy.optimize import brentq

# Gestion de la dépendance à numpy_financial
try:
    import numpy_financial as npf
    NPF_IS_REAL = True
except ImportError:
    NPF_IS_REAL = False
    print("AVERTISSEMENT MOTEUR: numpy_financial non trouvé. Fonctions secours utilisées.")

    # --- Fonctions Secours NPF (copiées depuis votre code original) ---
    def secours_npv(rate, values):
        """Fonction de secours pour NPV si numpy_financial n'est pas disponible."""
        # Assurer que values est un array numpy
        values = np.asarray(values)
        # Gérer le cas où le taux est exactement -1
        if abs(rate - (-1.0)) < 1e-9:
            # Si rate est -1, la somme diverge à l'infini si une valeur != 0 existe après T0
            if len(values) > 1 and np.any(values[1:] != 0):
                return float('-inf')
            # Si rate est -1 et toutes les valeurs futures sont 0, NPV = valeur T0
            elif len(values) > 0:
                 return values[0]
            else:
                 return 0.0 # Si pas de valeurs
        # Gérer le cas où le taux est inférieur à -1 (non défini)
        if rate < -1.0:
            # On retourne -inf car le dénominateur change de signe, rendant l'interprétation difficile.
            # Le NPV standard n'est pas défini pour rate <= -1.
            print(f"AVERTISSEMENT NPV: Taux {rate:.4f} <= -1, NPV non défini, retour -inf.")
            return float('-inf')

        # Calcul standard NPV pour rate > -1
        with np.errstate(over='raise', invalid='raise'):
            try:
                # Créer les facteurs d'actualisation (1+r)^0, (1+r)^1, ...
                discount_factors = (1 + rate) ** np.arange(len(values))

                # Gérer division par zéro si un facteur est nul (théoriquement impossible si rate > -1)
                if np.any(np.isclose(discount_factors, 0)):
                    print(f"AVERTISSEMENT NPV: Facteur d'actualisation nul rencontré pour taux {rate:.4f}.")
                    # Dépend du signe des flux futurs. Peut être +inf, -inf, ou fini.
                    # On retourne NaN pour indiquer un problème.
                    return np.nan

                # Calculer les valeurs actualisées
                pv = values / discount_factors

                # Gérer les cas d'overflow dans le calcul de pv
                if not np.all(np.isfinite(pv)):
                    print(f"AVERTISSEMENT NPV: Valeurs non finies (inf/nan) rencontrées dans PV pour taux {rate:.4f}.")
                    # Indique souvent une divergence
                    return np.nan

                # Sommer les valeurs actualisées
                return np.sum(pv)

            except (FloatingPointError, OverflowError) as e_fp:
                print(f"ERREUR NPV (FloatingPoint/Overflow) pour taux {rate:.4f}: {e_fp}")
                # Si une erreur numérique se produit, retourner NaN
                return np.nan
            except Exception as e_npv:
                 print(f"ERREUR NPV (Inconnue) pour taux {rate:.4f}: {e_npv}")
                 return np.nan

    # --- Fonction Secours IRR (Placeholder, vous devez l'implémenter si besoin) ---
    def secours_irr(values, guess=0.1):
        print("ERREUR MOTEUR: Fonction secours_irr non implémentée!")
        # Implémentez la logique avec brentq ou newton ici si numpy_financial n'est pas là
        # Example: from scipy.optimize import brentq
        # try:
        #    return brentq(lambda r: secours_npv(r, values), -0.9999, 1.0) # Cherche la racine de NPV(r)
        # except (ValueError, RuntimeError): #ValueError si pas de changement de signe, RuntimeError si échec solveur
        #    return np.nan # Ou une autre valeur pour indiquer échec
        return np.nan # Retourne NaN par défaut

    # Créer un module de remplacement
    class NpfModule:
        """Module de remplacement si numpy_financial n'est pas disponible."""
        @staticmethod
        def npv(rate, values): return secours_npv(rate, values)
        @staticmethod
        def irr(values): return secours_irr(values) # Utilise secours_irr

    npf = NpfModule() # Assigner le module de remplacement


class AnalysisEngine:
    """Moteur de calcul économique pur pour l'optimisation de l'autoconsommation collective."""

    def __init__(self, config: dict, scenarios: dict, sites_data: dict[str, pd.DataFrame]):
        """
        Initialise le moteur avec les données et configurations nécessaires.
        `sites_data` est un dictionnaire où les clés sont les identifiants de site (str)
        et les valeurs sont les DataFrames (pd.DataFrame) des données traitées pour ce site.
        """
        if not isinstance(config, dict): raise TypeError("config doit être un dict")
        if not isinstance(scenarios, dict): raise TypeError("scenarios doit être un dict")
        if not isinstance(sites_data, dict): raise TypeError("sites_data doit être un dict")
        if not sites_data: raise ValueError("sites_data ne peut pas être vide")

        # Valider les DataFrames dans sites_data
        required_cols = ['Temps', 'production_kwh', 'consumption_kwh']
        for site_id, df in sites_data.items():
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"L'élément pour le site '{site_id}' n'est pas un DataFrame")
            if df.empty:
                print(f"AVERTISSEMENT MOTEUR INIT: Le DataFrame pour le site '{site_id}' est vide.")
                # Optionnel: lever une erreur si un DF vide n'est pas acceptable
                # raise ValueError(f"Le DataFrame pour le site '{site_id}' est vide")
            # Vérifier que 'Temps' est de type datetime ou peut être converti
            if 'Temps' not in df.columns:
                 raise ValueError(f"Colonne 'Temps' manquante pour le site '{site_id}'")
            try:
                 # Essayer la conversion pour valider le format
                 pd.to_datetime(df['Temps'], errors='raise')
            except Exception as e_time:
                 raise ValueError(f"Colonne 'Temps' invalide pour site '{site_id}': {e_time}") from e_time

            # Vérifier les autres colonnes essentielles et leur type numérique
            for col in ['production_kwh', 'consumption_kwh']:
                 if col not in df.columns:
                      raise ValueError(f"Colonne '{col}' manquante pour le site '{site_id}'")
                 if not pd.api.types.is_numeric_dtype(df[col]):
                     try:
                          # Essayer la conversion en numérique
                          pd.to_numeric(df[col], errors='raise')
                     except Exception as e_num:
                          raise ValueError(f"Colonne '{col}' non numérique pour site '{site_id}': {e_num}") from e_num

        self.config = config
        self.scenarios = scenarios
        self.sites_data = sites_data
        self.npf_available = NPF_IS_REAL

    # --- calculate_wacc reste inchangé ---
    def calculate_wacc(self, debt_ratio, taux_interet_dette_pct, taux_imposition_pct, cout_fonds_propres_pct) -> float | None:
        """Calcule le WACC."""
        try:
            rd = float(taux_interet_dette_pct) / 100.0
            tc = float(taux_imposition_pct) / 100.0
            re = float(cout_fonds_propres_pct) / 100.0
            dr = float(debt_ratio)
            # Autoriser debt_ratio = 0 (100% Equity) ou 1 (100% Dette)
            if not (0 <= dr <= 1): raise ValueError("Debt ratio doit être entre 0 et 1")
            if not (0 <= tc < 1): raise ValueError("Taux imposition doit être >= 0 et < 100")
            # Vérifier que les taux sont non-négatifs
            if rd < 0: raise ValueError("Taux d'intérêt dette négatif invalide")
            if re < 0: raise ValueError("Coût fonds propres négatif invalide")

            cout_dette_apres_impots = rd * (1.0 - tc)
            equity_ratio = 1.0 - dr
            wacc = (dr * cout_dette_apres_impots) + (equity_ratio * re)

            if not np.isfinite(wacc):
                print(f"AVERTISSEMENT WACC: WACC non fini ({wacc}). Vérifiez les inputs.")
                return None
            return wacc
        except (TypeError, ValueError) as e:
            print(f"ERREUR MOTEUR (calculate_wacc): {e}")
            return None
        except Exception as e:
             print(f"ERREUR INATTENDUE (calculate_wacc): {e}")
             return None

    # --- Début de la fonction modifiée ---
    def calculate_financial_indicators(self, scenario_name: str, prix_revente: float | None = None, override_source_prix_autoconso: str | None = None) -> dict | None:
        """
        Calcule les indicateurs financiers pour un scénario donné SUR UNE BASE MENSUELLE.
        Retourne un dictionnaire avec un DataFrame mensuel et des indicateurs scalaires globaux.
        """
        start_time_calc = time.time()
        print(f"MOTEUR (Mensuel): Lancement calcul indicateurs pour '{scenario_name}'...")

        # --- DEBUT DEBUG --- 
        print(f"DEBUG ENGINE - Inside calculate_financial_indicators for '{scenario_name}'")
        print(f"  -> Using config value 'cout_fonds_propres': {self.config.get('cout_fonds_propres')}") # Use self.config here
        print(f"  -> Using config value 'capex': {self.config.get('capex')}")
        print(f"  -> Prix revente reçu: {prix_revente}")
        # --- FIN DEBUG --- 

        try:
            # --- 1. Récupération Config et Scénario ---
            if scenario_name not in self.scenarios:
                raise ValueError(f"Scénario '{scenario_name}' invalide.")
            scenario = self.scenarios[scenario_name]
            config = self.config # Utiliser la config locale passée ou self.config

            # --- 2. Validation/Conversion Paramètres Initiaux ---
            # (S'assurer que tous les paramètres nécessaires sont présents et convertis)
            required_keys = [
                 "date_debut_ppa", "duree_ppa", "taux_inflation", "taux_imposition",
                 "prix_vente_initial", "capex", "opex", "degradation_rate", "puissance_kwc",
                 "cout_fonds_propres", "with_loan", "tarif_oa", "tarif_edf_reference",
                 "tarif_oa_indexe_inflation", "taux_inflation_tarif_oa",
                 "amortissement_duree", "valeur_residuelle_pct",
                 "cout_demantelement_pct", "source_prix_autoconso",
                 "subvention_rate_le3", "subvention_rate_le9", "subvention_rate_le36",
                 "subvention_rate_le100", "subvention_rate_gt100",
                 "turpe_prod_calculee", "turpe_indexe_inflation"
            ]
            loan_keys = ["debt_ratio", "debt_term_years", "taux_interet_dette", "target_dscr"]
            missing_keys = [k for k in required_keys if config.get(k) is None]
            loan_active = config.get("with_loan", True)
            if loan_active: missing_keys.extend([k for k in loan_keys if config.get(k) is None])
            if missing_keys: raise ValueError(f"Paramètres config manquants: {missing_keys}")
            
            try:
                start_date_ppa = pd.to_datetime(config["date_debut_ppa"])
                num_months_simulation = int(config["duree_ppa"]) # Durée PPA est en MOIS
                if num_months_simulation <= 0: raise ValueError("Durée PPA doit être > 0 mois")
                
                # ---> AJOUTER CETTE LIGNE ICI <--- 
                simulation_years = num_months_simulation // 12 # Nombre entier d'années
                # Optionnel: Gérer si pas un multiple exact de 12 ? Pour l'instant, division entière.
                print(f"DEBUG MOTEUR: Nombre d'années de simulation: {simulation_years} (basé sur {num_months_simulation} mois)")
                # ---> FIN AJOUT <--- 

                capex_base = float(config["capex"]) # CAPEX total initial
                # Attention: opex dans config est ANNUEL
                opex_annual_base_config = float(config["opex"])

                # Valider et récupérer TOUS les paramètres nécessaires de la config
                required_keys = [
                     "date_debut_ppa", "duree_ppa", "taux_inflation", "taux_imposition",
                     "prix_vente_initial", "capex", "opex", "degradation_rate", "puissance_kwc",
                     "cout_fonds_propres", "with_loan", "tarif_oa", "tarif_edf_reference",
                     "tarif_oa_indexe_inflation", "taux_inflation_tarif_oa",
                     "amortissement_duree", "valeur_residuelle_pct", "cout_demantelement_pct",
                     "source_prix_autoconso", "subvention_rate_le3", "subvention_rate_le9",
                     "subvention_rate_le36", "subvention_rate_le100", "subvention_rate_gt100", # Utilise gt100 pour P>100
                     "turpe_prod_calculee", "turpe_indexe_inflation"
                ]
                loan_keys = ["debt_ratio", "debt_term_years", "taux_interet_dette", "target_dscr"] # Garder target_dscr ici
                missing_keys = [k for k in required_keys if config.get(k) is None]
                loan_active = config.get("with_loan", True)
                if loan_active: missing_keys.extend([k for k in loan_keys if config.get(k) is None])
                if missing_keys: raise ValueError(f"Paramètres config manquants: {', '.join(missing_keys)}")

                # Convertir les valeurs en types appropriés (avec gestion d'erreur)
                try:
                    # Paramètres de simulation
                    start_date_ppa_str = config["date_debut_ppa"]
                    try:
                         start_date_ppa = pd.to_datetime(start_date_ppa_str)
                    except ValueError as e_date:
                         raise ValueError(f"Format date_debut_ppa invalide ('{start_date_ppa_str}'): {e_date}") from e_date

                    num_months_simulation = int(config["duree_ppa"]) # Durée PPA est en MOIS
                    if num_months_simulation <= 0: raise ValueError("Durée PPA doit être > 0 mois")

                    # Paramètres économiques
                    capex_base = float(config["capex"])
                    opex_annual_base_config = float(config["opex"])
                    puissance_kwc_global = float(config["puissance_kwc"])
                    degradation_rate_base = float(config["degradation_rate"]) # Annuel
                    taux_inflation_pct = float(config["taux_inflation"])
                    adjusted_inflation_annual = taux_inflation_pct / 100.0 # Annuel
                    oa_indexed = bool(config["tarif_oa_indexe_inflation"])
                    inflation_rate_oa_pct = float(config.get("taux_inflation_tarif_oa", 1.5))
                    inflation_rate_oa_annual = inflation_rate_oa_pct / 100.0 # Annuel
                    tarif_oa_base = float(config["tarif_oa"])
                    turpe_annual_base_config = float(config.get("turpe_prod_calculee", 0.0))
                    turpe_indexed = bool(config.get("turpe_indexe_inflation", False))

                    # Paramètres financiers
                    taux_imposition_pct = float(config["taux_imposition"])
                    taux_imposition_annual = taux_imposition_pct / 100.0 # Annuel
                    amortissement_duree_years = int(config["amortissement_duree"])
                    if amortissement_duree_years <= 0: raise ValueError("Durée amortissement doit être > 0 ans")
                    valeur_residuelle_pct_config = float(config.get("valeur_residuelle_pct", 0.0)) / 100.0
                    cout_demantelement_pct_config = float(config.get("cout_demantelement_pct", 0.0)) / 100.0
                    cout_fonds_propres_pct_config = float(config.get("cout_fonds_propres", 8.0))

                    # Paramètres de prêt (conditionnel)
                    debt_ratio_config = float(config.get("debt_ratio", 0.80)) if loan_active else 0.0
                    debt_term_years_config = int(config.get("debt_term_years", 15)) if loan_active else 0
                    taux_interet_dette_pct_config = float(config.get("taux_interet_dette", 4.0)) if loan_active else 0.0
                    taux_interet_dette_annual = taux_interet_dette_pct_config / 100.0

                    # Paramètres de valorisation
                    source_prix_autoc_config = config.get("source_prix_autoconso", "prix_initial")
                    prix_vente_config = float(config["prix_vente_initial"])
                    tarif_edf_ref_config = float(config["tarif_edf_reference"])

                    # Subventions (garder les clés originales pour l'instant)
                    sub_rates = {
                         'le3': float(config.get("subvention_rate_le3", 0.0)),
                         'le9': float(config.get("subvention_rate_le9", 0.0)),
                         'le36': float(config.get("subvention_rate_le36", 0.0)),
                         'le100': float(config.get("subvention_rate_le100", 0.0)),
                         'gt100': float(config.get("subvention_rate_gt100", 0.0)) # Pour > 100
                    }

                except (ValueError, TypeError, KeyError) as e:
                    raise ValueError(f"Erreur de type/valeur dans la configuration: {e}") from e


                # --- Application modificateurs scénario ---
                capex_scenario = capex_base * float(scenario.get("capex_modifier", 1.0))
                opex_annual_base = opex_annual_base_config * float(scenario.get("opex_modifier", 1.0))
                turpe_annual_base = turpe_annual_base_config # La TURPE lue est déjà calculée, on applique juste l'indexation annuelle plus tard
                adjusted_inflation_scenario = adjusted_inflation_annual * float(scenario.get("inflation_modifier", 1.0))
                degradation_rate_scenario = degradation_rate_base * float(scenario.get("degradation_modifier", 1.0)) # Appliquer le modificateur ici
                production_modifier_scenario = float(scenario.get("production_modifier", 1.0))

                # --- Déterminer Prix/Source à Utiliser ---
                prix_vente_a_utiliser = float(prix_revente) if prix_revente is not None else prix_vente_config
                source_prix_autoc = override_source_prix_autoconso if override_source_prix_autoconso is not None else source_prix_autoc_config


                # --- 2. Agrégation Données Énergétiques (VÉRIFIER CETTE PARTIE) ---
                # Cette partie dépend de comment `self.sites_data` est structuré et si l'agrégation
                # doit être refaite ici ou si elle a déjà eu lieu.
                # Basé sur le code fourni, `calculate_financial_indicators` reçoit `sites_data`.
                # Il faut donc réaliser l'agrégation ici.

                if not self.sites_data:
                     raise ValueError("Aucune donnée de site disponible pour l'analyse.")

                print(f"MOTEUR (Mensuel): Agrégation des données pour {len(self.sites_data)} site(s)...")

                all_dfs = list(self.sites_data.values())
                if not all_dfs:
                    raise ValueError("Dictionnaire sites_data vide.")

                # Trouver la plage de dates commune ou globale
                min_date = min(df['Temps'].min() for df in all_dfs if not df.empty)
                max_date = max(df['Temps'].max() for df in all_dfs if not df.empty)

                # Créer un index commun à la résolution la plus fine trouvée (supposition: horaire ou mieux)
                # Essayer de détecter la fréquence
                freq = pd.infer_freq(all_dfs[0]['Temps'].sort_values())
                if freq is None:
                     time_diffs = all_dfs[0]['Temps'].sort_values().diff().dropna()
                     if not time_diffs.empty:
                          median_diff = time_diffs.median()
                          freq = pd.tseries.frequencies.to_offset(median_diff)
                          if freq is None:
                               print("AVERTISSEMENT MOTEUR: Impossible de déterminer la fréquence, agrégation peut être imprécise.")
                               # Utiliser une fréquence par défaut (ex: horaire) ou lever une erreur
                               freq = 'H' # Fallback à horaire
                     else:
                          freq = 'H' # Fallback si pas assez de points pour diff

                print(f"DEBUG MOTEUR: Fréquence détectée/utilisée pour l'agrégation: {freq}")
                
                common_index = pd.date_range(start=min_date, end=max_date, freq=freq)
                
                # Initialiser le DataFrame agrégé avec l'index commun
                data_agg = pd.DataFrame(0.0, index=common_index, columns=['production_kwh', 'consumption_kwh'])

                # Somme pondérée ou simple somme ? Pour l'instant, somme simple.
                for site_id, df_site in self.sites_data.items():
                     if df_site.empty: continue
                     # S'assurer que l'index est datetime et unique
                     df_temp = df_site.set_index('Temps')
                     if not isinstance(df_temp.index, pd.DatetimeIndex):
                          df_temp.index = pd.to_datetime(df_temp.index)
                     if df_temp.index.has_duplicates:
                          # print(f"AVERTISSEMENT MOTEUR: Doublons temporels agrégation site {site_id}. Somme.")
                          df_temp = df_temp.groupby(df_temp.index).sum()

                     # Réindexer sur l'index commun et additionner
                     # Utiliser fill_value=0 pour les pas de temps manquants
                     data_agg = data_agg.add(df_temp[['production_kwh', 'consumption_kwh']].reindex(common_index, fill_value=0.0), fill_value=0.0)

                # Réinitialiser l'index pour avoir la colonne 'Temps'
                data_agg = data_agg.reset_index().rename(columns={'index': 'Temps'})

                if data_agg.empty:
                    raise ValueError("Les données agrégées sont vides après la fusion.")
                print(f"MOTEUR (Mensuel): Données agrégées prêtes ({len(data_agg)} lignes).")
                # --- FIN AGRÉGATION ---

                # --- 3. Préparation de la Structure Mensuelle --- 
                num_months_simulation = simulation_years * 12
                # Créer l'index mensuel (fin de mois)
                try:
                    # Utiliser la date de début PPA comme point de départ
                    # Corriger l'avertissement de dépréciation M -> ME
                    monthly_index = pd.date_range(start=start_date_ppa, periods=num_months_simulation, freq='ME') # Utiliser 'ME'
                except ValueError as e_date_range:
                    # Fournir plus de contexte si la date de début est le problème
                    raise ValueError(f"Erreur création index mensuel à partir de start_date_ppa={start_date_ppa}: {e_date_range}") from e_date_range

                monthly_results_df = pd.DataFrame(index=monthly_index)

                # Définir les colonnes attendues (Vérification/Ajout des nouvelles)
                monthly_cols = [
                    'Year_Index', 'Sim_Year', 'Inflation_Factor', 'Degradation_Factor',
                    'Production_kWh', 'Consommation_kWh', 'Autoconsommation_kWh', 'Surplus_kWh',
                    'Tarif_OA_Annuel', 'Prix_Autoconso_Annuel',
                    'Revenus_Surplus', 'Revenus_Autoconsommation', 'Revenus_Total',
                    'OPEX', 'TURPE',
                    'Amortissement',        # <= Assurer présence
                    'EBITDA', 'EBIT',
                    'Interets_Payes', 'Principal_Rembourse', 'EBT',
                    'Impots_Provisionnes',  # <= Assurer présence
                    'Resultat_Net',
                    'FCFE',
                    'OCF_Projet',           # <= Assurer présence
                    'Solde_Dette_Fin_Mois', 'Service_Dette'
                ]
                for col in monthly_cols:
                    monthly_results_df[col] = 0.0 # Initialiser avec des flottants

                # --- 4. Calculs Préliminaires Annuels/Globaux ---
                # Calcul subvention (basé sur puissance globale et barèmes)
                applicable_sub_rate = 0.0
                if puissance_kwc_global <= 3: applicable_sub_rate = sub_rates['le3']
                elif puissance_kwc_global <= 9: applicable_sub_rate = sub_rates['le9']
                elif puissance_kwc_global <= 36: applicable_sub_rate = sub_rates['le36']
                elif puissance_kwc_global <= 100: applicable_sub_rate = sub_rates['le100']
                else: applicable_sub_rate = sub_rates['gt100'] # Utiliser gt100 pour P > 100
                total_subvention = applicable_sub_rate * puissance_kwc_global

                # --- DEBUT MODIFICATION: Calcul Dette/Equity sur CAPEX Net ---
                # Calculer CAPEX net AVANT calcul dette/equity
                capex_net_subvention = max(0, capex_scenario - total_subvention)
                print(f"DEBUG MOTEUR: CAPEX Scénario={capex_scenario:.2f}, Subvention={total_subvention:.2f}, CAPEX Net={capex_net_subvention:.2f}")

                # Calcul dette, equity sur le CAPEX NET
                debt_amount = capex_net_subvention * debt_ratio_config if loan_active else 0.0
                equity_amount = capex_net_subvention * (1.0 - debt_ratio_config) # Equity nécessaire pour financer le NET
                print(f"DEBUG MOTEUR: Dette={debt_amount:.2f}, Equity={equity_amount:.2f} (basés sur CAPEX Net)")

                # L'investissement T0 pour l'equity est maintenant simplement l'equity_amount calculé sur le net
                net_equity_investment = equity_amount
                print(f"DEBUG MOTEUR: Investissement Equity Net T0 = {net_equity_investment:.2f}")
                # --- FIN MODIFICATION ---

                # Calcul échéancier de prêt MENSUEL (Choix 2A)
                if loan_active and debt_amount > 1e-6:
                    monthly_interest_paid, monthly_principal_paid, monthly_debt_balance = self.calculate_monthly_loan_schedule(
                        debt_amount, taux_interet_dette_annual, debt_term_years_config, num_months_simulation
                    )
                else: # Pas de prêt
                    zeros_array = np.zeros(num_months_simulation)
                    monthly_interest_paid = zeros_array.copy()
                    monthly_principal_paid = zeros_array.copy()
                    monthly_debt_balance = zeros_array.copy() # Solde nul si pas de dette

                # Calcul amortissement annuel de base (pour allocation mensuelle)
                base_amortissable = capex_net_subvention * (1 - valeur_residuelle_pct_config)
                annual_depreciation_base = 0.0
                if amortissement_duree_years > 0:
                    annual_depreciation_base = base_amortissable / amortissement_duree_years

                # --- Fin Préparation Échéancier Dette --- 

                # --- Préparation des données de référence annuelles ---
                # Identifier l'année de référence dans les données agrégées
                # S'assurer que data_agg est bien indexé par Temps ici
                if not isinstance(data_agg.index, pd.DatetimeIndex):
                     # Tenter la conversion si ce n'est pas le cas
                     try:
                          if 'Temps' in data_agg.columns:
                               data_agg = data_agg.set_index('Temps')
                          elif data_agg.index.name == 'Temps':
                               data_agg.index = pd.to_datetime(data_agg.index)
                          else:
                               raise ValueError("Impossible de définir DatetimeIndex pour data_agg")
                     except Exception as e_idx:
                          raise ValueError(f"Erreur lors de la définition de l'index Temps pour data_agg: {e_idx}") from e_idx
                
                if data_agg.empty:
                     raise ValueError("data_agg est vide avant la préparation des données de référence.")

                ref_year = data_agg.index.year.min() # Utiliser la première année des données comme référence
                # Créer un DataFrame de référence contenant uniquement les données de cette année
                reference_data_ts = data_agg[data_agg.index.year == ref_year].copy() # Utiliser .copy() pour éviter SettingWithCopyWarning
                if reference_data_ts.empty:
                     raise ValueError(f"Aucune donnée trouvée pour l'année de référence {ref_year} dans data_agg.")
                print(f"MOTEUR (Mensuel): Année de référence pour profil énergétique: {ref_year}")
                # --- Fin Préparation Référence ---
                
                # --- DEBUG: Vérifier reference_data_ts --- 
                print("DEBUG: Affichage tête données référence (reference_data_ts):")
                print(reference_data_ts.head())
                print(reference_data_ts.info()) # Pour vérifier le type de l'index et des colonnes
                # --- FIN DEBUG ---

                # --- 5. Boucle Mensuelle Principale ---
                loss_carryforward_balance = 0.0
                current_year_tracker = -1
                annual_tax_calculated_prev_year = 0.0 # Impôt calculé pour N-1, provisionné en N

                # ---> Initialisation des variables annuelles AVANT la boucle <---
                #     (Valeurs pour l'année 1 / index 0)
                inflation_factor_year = 1.0 # Année 1 (index 0)
                degradation_factor_year = 1.0 # Année 1 (index 0)
                opex_current_year = opex_annual_base # Année 1 = base
                turpe_current_year = turpe_annual_base # Année 1 = base
                depreciation_current_year = annual_depreciation_base if 0 < amortissement_duree_years else 0.0
                current_oa_rate_annual = tarif_oa_base # Année 1 = base
                # Calcul Prix Autoconso Annuel pour l'année 1 (index 0)
                if source_prix_autoc == 'prix_initial': current_prix_autoc_annual = prix_vente_a_utiliser * 1.0 # inflation_factor_year = 1 pour an 1
                elif source_prix_autoc == 'tarif_edf': current_prix_autoc_annual = tarif_edf_ref_config * 1.0
                elif source_prix_autoc == 'tarif_oa': current_prix_autoc_annual = current_oa_rate_annual # Utilise OA base an 1
                else: current_prix_autoc_annual = prix_vente_a_utiliser * 1.0

                # Utiliser num_months_simulation ici qui est défini plus haut
                for month_idx in range(num_months_simulation):
                    # --- OBTENIR LA DATE DE FIN DE MOIS CORRESPONDANTE ---
                    # 'monthly_index' a été créé plus tôt avec pd.date_range(..., freq='ME')
                    current_month_end_date = monthly_index[month_idx]

                    # --- Calculs/Détections liés à l'année (utiliser current_month_end_date) ---
                    year_idx = current_month_end_date.year - start_date_ppa.year # Index année (0, 1, 2...)
                    simulation_year = year_idx + 1 # Année de simulation (1, 2, 3...)
                    # Stocker les index/années dans le DataFrame (utiliser current_month_end_date comme clé)
                    # La vérification if current_month_end_date in monthly_results_df.index: n'est plus nécessaire
                    # car on utilise directement l'index qui existe.
                    monthly_results_df.loc[current_month_end_date, 'Year_Index'] = year_idx
                    monthly_results_df.loc[current_month_end_date, 'Sim_Year'] = simulation_year
                    # --- Suppression de l'ancienne vérification ---
                    # if month_date in monthly_results_df.index:
                    #      monthly_results_df.loc[month_date, 'Year_Index'] = year_idx
                    #      monthly_results_df.loc[month_date, 'Sim_Year'] = simulation_year
                    # else:
                    #      print(f"ATTENTION: Date {month_date} non trouvée dans monthly_results_df.index, itération sautée.")
                    #      continue # Si la date n'est pas dans l'index, sauter

                    # --- Impression DÉBUT Itération (utiliser current_month_end_date pour l'affichage) ---
                    #print(f"\n--- DEBUG MOIS {month_idx+1}/{num_months_simulation} (Date: {current_month_end_date.strftime('%Y-%m-%d')}, Année Sim: {simulation_year}) ---")

                    # Détection de nouvelle année (utiliser current_month_end_date)
                    is_new_year = (current_month_end_date.year != current_year_tracker)
                    # Modification ici : Recalculer si nouvelle année, même pour la première année (year_idx == 0)
                    # pour initialiser current_year_tracker et éviter recalcul inutile si la première année a plusieurs mois.
                    if is_new_year:
                        new_year_detected = current_month_end_date.year
                        print(f"DEBUG Année {simulation_year}: Nouvelle année détectée ({new_year_detected} vs {current_year_tracker})")
                        
                        # Calcul Impôt Annuel (pour N-1) avant de mettre à jour le tracker
                        if year_idx > 0: # Seulement si ce n'est PAS la première année
                            last_full_year_date = current_year_tracker # L'année qui vient de se terminer
                            print(f"DEBUG Année {simulation_year}: Calcul impôt N-1 pour l'année {last_full_year_date}")
                            # Filtrer les données de l'année N-1 déjà calculées dans le DF
                            ebt_last_year_monthly = monthly_results_df.loc[monthly_results_df.index.year == last_full_year_date, 'EBT']
                            if not ebt_last_year_monthly.empty:
                                 ebt_last_year_sum = ebt_last_year_monthly.sum()
                                 print(f"DEBUG Année {simulation_year}: EBT N-1 ({last_full_year_date}) = {ebt_last_year_sum:.2f}, Report Déficitaire N-1 = {loss_carryforward_balance:.2f}")
                                 loss_used_last_year = min(loss_carryforward_balance, max(0, ebt_last_year_sum))
                                 taxable_ebt_last_year = ebt_last_year_sum - loss_used_last_year
                                 annual_tax_calculated_prev_year = max(0, taxable_ebt_last_year * taux_imposition_annual)
                                 loss_carryforward_balance -= loss_used_last_year
                                 if ebt_last_year_sum < 0: loss_carryforward_balance += abs(ebt_last_year_sum)
                                 print(f"DEBUG Année {simulation_year}: Déficit Utilisé N-1={loss_used_last_year:.2f}, Impôt N-1 calc={annual_tax_calculated_prev_year:.2f}, Nouveau Report Déficitaire={loss_carryforward_balance:.2f}")
                            else:
                                 print(f"DEBUG Année {simulation_year}: Pas de données EBT trouvées pour l'année {last_full_year_date}, impôt N-1 = 0")
                                 annual_tax_calculated_prev_year = 0.0 # Si pas de données pour N-1
                        else: # Première année, pas d'impôt N-1
                            print(f"DEBUG Année {simulation_year}: Première année, impôt N-1 = 0")
                            annual_tax_calculated_prev_year = 0.0

                        # Mise à jour du tracker de l'année courante APRES calcul impôt N-1
                        current_year_tracker = new_year_detected
                        print(f"DEBUG Année {simulation_year}: current_year_tracker mis à jour à {current_year_tracker}")

                        # Recalculer les facteurs et coûts annuels SEULEMENT si year_idx > 0
                        if year_idx > 0:
                            print(f"DEBUG Année {simulation_year}: Recalcul des facteurs/coûts annuels (car year_idx={year_idx} > 0)")
                            # Recalculer tous les facteurs et coûts annuels pour l'année en cours (year_idx)
                            inflation_factor_year = (1 + adjusted_inflation_scenario) ** year_idx
                            degradation_factor_year = (1 - degradation_rate_scenario) ** year_idx
                            opex_current_year = opex_annual_base * inflation_factor_year
                            turpe_current_year = turpe_annual_base * (inflation_factor_year if turpe_indexed else 1.0)
                            # Recalcul Amortissement Annuel
                            depreciation_current_year = annual_depreciation_base if year_idx < amortissement_duree_years else 0.0
                            # Recalcul OA et Prix Autoconso
                            # ... (logique recalcul prix) ...
                            current_oa_rate_annual = tarif_oa_base * ((1 + inflation_rate_oa_annual)**year_idx if oa_indexed else 1.0)
                            # --- AJOUT DEBUG ---
                            # print(f"DEBUG Année {simulation_year}: Recalc AVANT prix autoconso -> OpexAn={opex_current_year:.2f}, TurpeAn={turpe_current_year:.2f}")
                            # print(f"DEBUG Année {simulation_year}: Bases -> OpexBase={opex_annual_base}, TurpeBase={turpe_annual_base}")
                            # --- FIN AJOUT ---

                            # Recalculer Prix Autoconso Annuel
                            if source_prix_autoc == 'prix_initial': current_prix_autoc_annual = prix_vente_a_utiliser * inflation_factor_year
                            elif source_prix_autoc == 'tarif_edf': current_prix_autoc_annual = tarif_edf_ref_config * inflation_factor_year
                            elif source_prix_autoc == 'tarif_oa': current_prix_autoc_annual = current_oa_rate_annual
                            else: current_prix_autoc_annual = prix_vente_a_utiliser * inflation_factor_year
                        else:
                             # Pour la première année (year_idx == 0), les valeurs initialisées avant la boucle sont correctes.
                             print(f"DEBUG Année {simulation_year}: Pas de recalcul des facteurs/coûts (car year_idx={year_idx})")
                             pass # Les valeurs initiales sont déjà définies avant la boucle

                    # ---> Utilisation des variables DÉJÀ définies ou mises à jour <---

                    # --- Vérification Calculs Annuels (imprimer DANS la boucle après mise à jour potentielle) ---
                    print(f"  Facteurs An: Infl={inflation_factor_year:.4f}, Degrad={degradation_factor_year:.4f}")
                    print(f"  Coûts An: OPEX={opex_current_year:.2f}, TURPE={turpe_current_year:.2f}, Amort={depreciation_current_year:.2f}")
                    print(f"  Tarifs An: OA={current_oa_rate_annual:.4f}, AutoConso={current_prix_autoc_annual:.4f}")
                    print(f"  Impôt N-1 prov: {annual_tax_calculated_prev_year:.2f}") # Impôt calculé au début de l'année N, provisionné mensuellement en N

                    # --- Stocker facteurs annuels (utiliser current_month_end_date comme clé) ---
                    monthly_results_df.loc[current_month_end_date, 'Inflation_Factor'] = inflation_factor_year
                    monthly_results_df.loc[current_month_end_date, 'Degradation_Factor'] = degradation_factor_year # Utilise la valeur de l'année
                    monthly_results_df.loc[current_month_end_date, 'Tarif_OA_Annuel'] = current_oa_rate_annual # Utilise la valeur de l'année
                    monthly_results_df.loc[current_month_end_date, 'Prix_Autoconso_Annuel'] = current_prix_autoc_annual # Utilise la valeur de l'année

                    # --- Allocation Mensuelle des Coûts Annuels (utiliser current_month_end_date comme clé) ---
                    monthly_results_df.loc[current_month_end_date, 'OPEX'] = opex_current_year / 12.0
                    monthly_results_df.loc[current_month_end_date, 'TURPE'] = turpe_current_year / 12.0
                    # Utilisation du nom standard 'Amortissement'
                    monthly_results_df.loc[current_month_end_date, 'Amortissement'] = depreciation_current_year / 12.0
                    # Utilisation du nom standard 'Impots_Provisionnes'
                    monthly_results_df.loc[current_month_end_date, 'Impots_Provisionnes'] = annual_tax_calculated_prev_year / 12.0

                    # --- Calcul Énergie Mensuelle ---
                    # (Utiliser current_month_end_date.month)
                    sim_month = current_month_end_date.month # Le mois de la date de fin de mois
                    prod_month = 0.0 # Initialiser pour ce mois
                    cons_month = 0.0 # Initialiser pour ce mois
                    auto_month = 0.0 # Initialiser
                    surplus_month = 0.0 # Initialiser
                    try:
                        ref_month_start = datetime(ref_year, sim_month, 1)
                        ref_month_end_day = pd.Timestamp(ref_month_start).days_in_month
                        ref_month_end = datetime(ref_year, sim_month, ref_month_end_day, 23, 59, 59)
                        print(f"  Filtre Réf Date: {ref_month_start.strftime('%Y-%m-%d')} -> {ref_month_end.strftime('%Y-%m-%d')}")

                        # Tenter d'abord avec .loc pour performance, puis fallback
                        try:
                             ref_monthly_energy_data = reference_data_ts.loc[ref_month_start:ref_month_end]
                        except KeyError:
                             print(f"    AVERTISSEMENT: Filtrage .loc échoué (KeyError), tentative filtrage manuel.")
                             ref_monthly_energy_data = reference_data_ts[
                                  (reference_data_ts.index >= ref_month_start) &
                                  (reference_data_ts.index <= ref_month_end)
                             ]

                        print(f"  Shape Données Réf Mois: {ref_monthly_energy_data.shape}") # Clé: vérifier si (0, ...)

                        if not ref_monthly_energy_data.empty:
                            prod_ref_month_series = ref_monthly_energy_data.get('production_kwh', pd.Series(0.0, index=ref_monthly_energy_data.index))
                            cons_ref_month_series = ref_monthly_energy_data.get('consumption_kwh', pd.Series(0.0, index=ref_monthly_energy_data.index))
                            print(f"    Prod Réf Sum: {prod_ref_month_series.sum():.2f}") # Clé: vérifier si > 0
                            print(f"    Conso Réf Sum: {cons_ref_month_series.sum():.2f}")

                            prod_adj_month_series = prod_ref_month_series * degradation_factor_year * production_modifier_scenario
                            prod_month = prod_adj_month_series.sum()
                            cons_month = cons_ref_month_series.sum() # Somme de la référence
                            print(f"    Prod Mois AJUSTÉE: {prod_month:.2f}") # Clé: vérifier cette valeur finale
                            print(f"    Conso Mois: {cons_month:.2f}")

                            # Calcul Autoconso/Surplus basé sur PROFIL HORAIRE AJUSTÉ et conso réf horaire
                            auto_month_vector = np.minimum(prod_adj_month_series, cons_ref_month_series)
                            auto_month = auto_month_vector.sum()
                            surplus_month = prod_month - auto_month
                        else:
                             print(f"    AVERTISSEMENT: Aucune donnée de référence trouvée pour ce mois.")
                             # Les valeurs prod_month, cons_month etc. restent à 0

                    except Exception as e_eng:
                        print(f"    ERREUR Calcul Énergie: {e_eng}")
                        # Laisser les valeurs à 0 en cas d'erreur ici

                    # Stocker les volumes mensuels calculés (utiliser current_month_end_date comme clé)
                    monthly_results_df.loc[current_month_end_date, 'Production_kWh'] = prod_month
                    monthly_results_df.loc[current_month_end_date, 'Consommation_kWh'] = cons_month
                    monthly_results_df.loc[current_month_end_date, 'Autoconsommation_kWh'] = auto_month
                    monthly_results_df.loc[current_month_end_date, 'Surplus_kWh'] = surplus_month
                    # --- AJOUT DEBUG ---
                    # print(f"DEBUG Mois {current_month_end_date.month} (An Sim {simulation_year}): prod_month stocké = {prod_month:.2f}")
                    # --- FIN AJOUT ---

                    # --- Calcul Revenus Mensuels ---
                    # Utilise current_oa_rate_annual et current_prix_autoc_annual qui sont définis pour l'année courante
                    revenue_surplus = surplus_month * current_oa_rate_annual
                    revenue_autoconsommation = auto_month * current_prix_autoc_annual
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Surplus'] = revenue_surplus
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Autoconsommation'] = revenue_autoconsommation
                    monthly_results_df.loc[current_month_end_date, 'Revenus_Total'] = revenue_surplus + revenue_autoconsommation

                    # --- Calcul P&L Mensuel ---
                    ebitda_mois = (monthly_results_df.loc[current_month_end_date, 'Revenus_Total']
                                   - monthly_results_df.loc[current_month_end_date, 'OPEX']
                                   - monthly_results_df.loc[current_month_end_date, 'TURPE'])
                    monthly_results_df.loc[current_month_end_date, 'EBITDA'] = ebitda_mois

                    ebit_mois = ebitda_mois - monthly_results_df.loc[current_month_end_date, 'Amortissement']
                    monthly_results_df.loc[current_month_end_date, 'EBIT'] = ebit_mois

                    # Récupérer Intérêts et Principal du mois depuis l'échéancier
                    interest_this_month = monthly_interest_paid[month_idx] if month_idx < len(monthly_interest_paid) else 0.0
                    principal_this_month = monthly_principal_paid[month_idx] if month_idx < len(monthly_principal_paid) else 0.0
                    monthly_results_df.loc[current_month_end_date, 'Interets_Payes'] = interest_this_month
                    monthly_results_df.loc[current_month_end_date, 'Principal_Rembourse'] = principal_this_month

                    ebt_mois = ebit_mois - interest_this_month
                    monthly_results_df.loc[current_month_end_date, 'EBT'] = ebt_mois

                    # Calculer le Résultat Net mensuel (EBT - Impôts Provisionnés)
                    # C'est une vision "cash" pour les flux, l'impôt réel est annuel.
                    resultat_net_mois = ebt_mois - monthly_results_df.loc[current_month_end_date, 'Impots_Provisionnes']
                    monthly_results_df.loc[current_month_end_date, 'Resultat_Net'] = resultat_net_mois

                    # --- Calcul Flux Mensuels ---
                    # FCFE = Net Income + Depreciation - Principal Repayment (+/- Changes in WC, non modélisé ici)
                    fcfe_mois = (resultat_net_mois
                                 + monthly_results_df.loc[current_month_end_date, 'Amortissement']
                                 - principal_this_month)
                    monthly_results_df.loc[current_month_end_date, 'FCFE'] = fcfe_mois

                    # OCF Projet = EBIT * (1 - Tax Rate) + Depreciation
                    # Ou = EBITDA * (1 - Tax Rate) + (Depreciation * Tax Rate) <- Formule utilisée dans le concept
                    # Utilisons la seconde pour être cohérent avec le concept :
                    amortissement_mois = monthly_results_df.loc[current_month_end_date, 'Amortissement']
                    ocf_projet_mois = (ebitda_mois * (1.0 - taux_imposition_annual)) + (amortissement_mois * taux_imposition_annual)
                    monthly_results_df.loc[current_month_end_date, 'OCF_Projet'] = ocf_projet_mois

                    # --- AJOUT : Calcul et stockage Service Dette Mensuel ---
                    service_dette_mois = interest_this_month + principal_this_month
                    monthly_results_df.loc[current_month_end_date, 'Service_Dette'] = service_dette_mois
                    # --- FIN AJOUT ---

                    # Solde Dette fin de mois (utiliser current_month_end_date comme clé)
                    debt_balance_this_month = monthly_debt_balance[month_idx] if month_idx < len(monthly_debt_balance) else 0.0
                    monthly_results_df.loc[current_month_end_date, 'Solde_Dette_Fin_Mois'] = debt_balance_this_month

                # --- Fin de la boucle Mensuelle ---

                # --- 6. Calcul des Indicateurs Scalaires Globaux (post-boucle) ---

                # Créer le flux de cash FCFE pour IRR/NPV Equity (T0 + flux mensuels)
                fcfe_monthly_array = monthly_results_df['FCFE'].fillna(0).values # Remplacer NaN par 0 pour calculs
                # L'investissement initial T0 est net_equity_investment (négatif)
                equity_cash_flows_monthly = np.concatenate(([-net_equity_investment], fcfe_monthly_array))

                # Créer le flux de cash OCF pour IRR/NPV Projet (T0 + flux mensuels + ajustement final)
                ocf_monthly_array = monthly_results_df['OCF_Projet'].fillna(0).values
                # L'investissement initial T0 est le CAPEX brut (négatif)
                project_cash_flow_t0 = -capex_scenario

                # Ajuster le dernier flux OCF mensuel pour valeur résiduelle et démantèlement
                if len(ocf_monthly_array) > 0:
                    valeur_residuelle_amount = capex_net_subvention * valeur_residuelle_pct_config
                    cout_demantelement_amount = capex_scenario * cout_demantelement_pct_config
                    terminal_value_adjustment = valeur_residuelle_amount - cout_demantelement_amount
                    # Ajouter l'ajustement au DERNIER mois de la simulation
                    ocf_monthly_array[-1] += terminal_value_adjustment
                else:
                     terminal_value_adjustment = 0 # Si pas de mois simulé

                project_cash_flows_monthly = np.concatenate(([project_cash_flow_t0], ocf_monthly_array))

                # Calcul WACC Annuel (inchangé)
                wacc_annual = self.calculate_wacc(
                     debt_ratio=debt_ratio_config,
                     taux_interet_dette_pct=taux_interet_dette_pct_config,
                     taux_imposition_pct=taux_imposition_pct,
                     cout_fonds_propres_pct=cout_fonds_propres_pct_config
                )

                # Calculer Taux MENSUEL équivalent pour NPV
                wacc_monthly = None  # <--- INITIALISER ICI !

                if wacc_annual is not None and wacc_annual > -1.0: # WACC doit être > -100%
                     try:
                          wacc_monthly = (1 + wacc_annual)**(1/12) - 1
                          # --- AJOUT Vérification isfinite ---
                          if not np.isfinite(wacc_monthly):
                               print(f"AVERTISSEMENT MOTEUR: WACC mensuel calculé non fini ({wacc_monthly}). Remis à None.")
                               wacc_monthly = None
                          # --- FIN AJOUT ---
                     except ValueError: # Peut arriver si 1+wacc_annual est négatif
                          print(f"AVERTISSEMENT MOTEUR: Impossible de calculer WACC mensuel à partir de WACC annuel {wacc_annual:.4f}.")
                          wacc_monthly = None # Assurer que c'est None en cas d'erreur
                else:
                     print("AVERTISSEMENT MOTEUR: WACC Annuel invalide ou non calculable, impossible de dériver WACC mensuel.")
                     # wacc_monthly est déjà None grâce à l'initialisation

                # --- DEBUT DEBUG WACC (Peut rester tel quel ou améliorer l'affichage de None) ---
                print(f"DEBUG ENGINE - WACC Calculation:")
                print(f"  -> Inputs: debt_ratio={debt_ratio_config}, int_debt%={taux_interet_dette_pct_config}, tax%={taux_imposition_pct}, cost_equity%={cout_fonds_propres_pct_config}")
                # Afficher 'N/A' si None pour plus de clarté
                wacc_annual_str = f"{wacc_annual:.6f}" if wacc_annual is not None else "N/A"
                wacc_monthly_str = f"{wacc_monthly:.6f}" if wacc_monthly is not None else "N/A"
                print(f"  -> Result: wacc_annual={wacc_annual_str}, wacc_monthly={wacc_monthly_str}")
                # --- FIN DEBUG WACC ---

                # --- DEBUT AJOUT: Calcul Taux Fonds Propres Mensuel (Re) ---
                re_annual = cout_fonds_propres_pct_config / 100.0
                re_monthly = None # Initialiser à None
                if re_annual > -1.0: # Vérifier validité taux annuel
                    try:
                        re_monthly = (1 + re_annual)**(1/12) - 1
                        if not np.isfinite(re_monthly):
                             print(f"AVERTISSEMENT MOTEUR: Taux Re mensuel calculé non fini ({re_monthly}). Remis à None.")
                             re_monthly = None
                    except ValueError:
                         print(f"AVERTISSEMENT MOTEUR: Impossible de calculer Re mensuel à partir de Re annuel {re_annual:.4f}.")
                         re_monthly = None # Assurer que c'est None en cas d'erreur
                else:
                     print(f"AVERTISSEMENT MOTEUR: Taux Re Annuel invalide ({re_annual}), impossible de dériver Re mensuel.")

                print(f"DEBUG ENGINE - Cost of Equity Rate (Re): re_annual={re_annual:.6f}, re_monthly={re_monthly if re_monthly is not None else 'N/A'}")
                # --- FIN AJOUT ---

                # Calculer IRR Equity (fonctionne sur les flux périodiques, ici mensuels)
                irr_equity = np.nan
                if len(equity_cash_flows_monthly) > 1 and np.any(equity_cash_flows_monthly): # Assurer qu'il y a des flux non nuls
                     try:
                          irr_equity_raw = npf.irr(equity_cash_flows_monthly)
                          # Convertir IRR mensuel en IRR annuel: (1 + irr_mensuel)^12 - 1
                          irr_equity = (1 + irr_equity_raw)**12 - 1 if np.isfinite(irr_equity_raw) else np.nan
                     except Exception as e_irr:
                          print(f"AVERTISSEMENT MOTEUR (IRR Equity): {e_irr}")
                          irr_equity = np.nan # Ou None selon préférence
                else:
                     print("AVERTISSEMENT MOTEUR: Flux Equity insuffisants/nuls pour calcul IRR.")

                # Calculer NPV Equity (utilise le taux MENSUEL Re et les flux MENSUELS)
                npv_equity = np.nan
                if re_monthly is not None and abs(1 + re_monthly) > 1e-12: # Taux Re != -1
                       try:
                           print(f"DEBUG NPV EQUITY: Utilisation taux re_monthly = {re_monthly:.8f}")
                           # --- Assurer que npv utilise re_monthly --- 
                           npv_equity = npf.npv(re_monthly, equity_cash_flows_monthly) # Utilise re_monthly
                           # -------------------------------------------
                           if not np.isfinite(npv_equity): npv_equity = np.nan
                       except Exception as e_npv:
                           print(f"AVERTISSEMENT MOTEUR (NPV Equity Mensuel @ Re): {e_npv}")
                           npv_equity = np.nan
                else:
                      print("AVERTISSEMENT MOTEUR: Taux Re mensuel invalide pour calcul NPV Equity.")
                      npv_equity = np.nan

                # Calculer ROI Equity
                roi_equity = np.nan
                if np.isfinite(npv_equity) and abs(net_equity_investment) > 1e-9:
                     roi_equity = npv_equity / net_equity_investment

                # Calculer Payback Equity (en mois, puis converti en années)
                payback_equity_months = self.calculate_payback_months(equity_cash_flows_monthly)
                payback_equity_years = payback_equity_months / 12.0 if payback_equity_months is not None else np.nan

                # Calculer IRR Projet (converti en annuel)
                irr_project = np.nan
                if len(project_cash_flows_monthly) > 1 and np.any(project_cash_flows_monthly):
                     try:
                          irr_project_raw = npf.irr(project_cash_flows_monthly)
                          irr_project = (1 + irr_project_raw)**12 - 1 if np.isfinite(irr_project_raw) else np.nan
                     except Exception as e_irr_proj:
                          print(f"AVERTISSEMENT MOTEUR (IRR Projet): {e_irr_proj}")
                          irr_project = np.nan
                else:
                      print("AVERTISSEMENT MOTEUR: Flux Projet insuffisants/nuls pour calcul IRR.")


                # Calculer NPV Projet (utilise WACC MENSUEL et flux MENSUELS)
                npv_project = np.nan
                if wacc_monthly is not None and abs(1 + wacc_monthly) > 1e-12:
                     try:
                          npv_project = npf.npv(wacc_monthly, project_cash_flows_monthly)
                          if not np.isfinite(npv_project): npv_project = np.nan
                     except Exception as e_npv_proj:
                          print(f"AVERTISSEMENT MOTEUR (NPV Projet Mensuel): {e_npv_proj}")
                          npv_project = np.nan
                else:
                     print("AVERTISSEMENT MOTEUR: WACC mensuel invalide pour calcul NPV Projet.")


                # Calculer Payback Projet (en mois, puis converti en années)
                payback_project_months = self.calculate_payback_months(project_cash_flows_monthly)
                payback_project_years = payback_project_months / 12.0 if payback_project_months is not None else np.nan

                # Calcul LCOE (utilise WACC mensuel et données mensuelles)
                lcoe = self.calculate_lcoe_monthly(wacc_monthly, capex_net_subvention, monthly_results_df)

                # Calcul DSCR Moyen (agrégation par année des données mensuelles)
                avg_dscr = self.calculate_avg_dscr_from_monthly(monthly_results_df)

                # Calcul Taux Autoconso/Autoprod Moyens (basé sur totaux mensuels)
                total_production = monthly_results_df['Production_kWh'].sum()
                total_consumption = monthly_results_df['Consommation_kWh'].sum()
                total_autoconsumption = monthly_results_df['Autoconsommation_kWh'].sum()
                autoconsumption_rate = (total_autoconsumption / total_consumption) if total_consumption > 1e-6 else 0.0
                autoproduction_rate = (total_autoconsumption / total_production) if total_production > 1e-6 else 0.0

                # --- AJOUT DEBUG LCOE INPUTS ---
                print(f"DEBUG LCOE INPUTS: WACC Annuel = {wacc_annual}")
                print(f"DEBUG LCOE INPUTS: WACC Mensuel = {wacc_monthly}")
                print(f"DEBUG LCOE INPUTS: CAPEX Net Subvention (T0 pour LCOE) = {capex_net_subvention}")
                total_prod_kwh = monthly_results_df['Production_kWh'].sum()
                print(f"DEBUG LCOE INPUTS: Production Totale (non actualisée) = {total_prod_kwh} kWh")
                total_opex = monthly_results_df['OPEX'].sum()
                total_turpe = monthly_results_df['TURPE'].sum()
                print(f"DEBUG LCOE INPUTS: OPEX Total (non actualisé) = {total_opex}")
                print(f"DEBUG LCOE INPUTS: TURPE Total (non actualisé) = {total_turpe}")
                # --- FIN AJOUT DEBUG ---

                # --- 7. Construction du Dictionnaire de Résultats (Choix 5) ---
                results = {
                    # Indicateurs Scalaires Globaux
                    "scenario": scenario_name, "prix_revente": prix_vente_a_utiliser,
                    "capex": capex_scenario, # CAPEX utilisé pour ce scénario
                    "equity_amount": equity_amount, "debt_amount": debt_amount,
                    "total_subvention": total_subvention,
                    "net_equity_investment": net_equity_investment, # T0 Equity
                    "autoconsumption_rate": autoconsumption_rate,
                    "autoproduction_rate": autoproduction_rate,
                    "wacc": wacc_annual, # WACC Annuel
                    "lcoe": lcoe, # LCOE calculé sur base mensuelle

                    # Indicateurs Equity
                    "irr": irr_equity, # TRI Equity (Annuel)
                    "npv": npv_equity, # NPV Equity (Actualisée mensuellement)
                    "roi": roi_equity, # ROI Equity
                    "payback_period": payback_equity_years, # Payback Equity (Années)

                    # Indicateurs Projet
                    "irr_project": irr_project, # TRI Projet (Annuel)
                    "npv_project": npv_project, # NPV Projet (Actualisée mensuellement)
                    "payback_project": payback_project_years, # Payback Projet (Années)

                    "avg_dscr": avg_dscr, # DSCR Moyen (basé sur aggrégation annuelle)
                    
                    # Données Mensuelles Détaillées
                    "monthly_data": monthly_results_df # Le DataFrame avec index mensuel
                    # Optionnel : ajouter les arrays de cash flow pour debug
                    # "debug_equity_cash_flows_monthly": equity_cash_flows_monthly.tolist(),
                    # "debug_project_cash_flows_monthly": project_cash_flows_monthly.tolist()
                }

                # --- DEBUT DEBUG NPV ---
                print(f"DEBUG ENGINE - Final Results Calculation:")
                print(f"  -> NPV Equity Calculated: {results.get('npv')}")
                print(f"  -> IRR Equity Calculated: {results.get('irr')}")
                print(f"  -> LCOE Calculated: {results.get('lcoe')}")
                # --- FIN DEBUG NPV ---

                end_time_calc = time.time()
                print(f"MOTEUR (Mensuel): Indicateurs calculés pour '{scenario_name}' en {end_time_calc - start_time_calc:.3f} sec.")
                return results

            except (ValueError, TypeError) as e:
                print(f"ERREUR MOTEUR (Mensuel - Validation/Préparation) pour '{scenario_name}': {e}")
                raise e # Renvoyer l'erreur pour indiquer un problème de config/données
            except Exception as e:
                print(f"ERREUR MOTEUR INATTENDUE (Mensuel): {e}")
                print(traceback.format_exc())
                # Pourrait retourner None ici ou renvoyer une RuntimeError
                raise RuntimeError(f"Erreur inattendue Moteur Mensuel: {e}") from e

        except (ValueError, TypeError, RuntimeError) as e:
            print(f"ERREUR MOTEUR (simulate_selling_price - Mensuel): {e}")
            raise e # Renvoyer pour que l'UI gère
        except Exception as e:
            print(f"ERREUR MOTEUR INATTENDUE (simulate_selling_price - Mensuel): {e}")
            traceback.print_exc()
            raise RuntimeError(f"Erreur inattendue lors de la simulation du prix (base mensuelle) : {e}") from e

    # --- Fonctions Helper (intégrées comme méthodes de la classe) ---

    def calculate_monthly_loan_schedule(self, principal, annual_rate, term_years, num_months_simulation):
        """Calcule l'échéancier mensuel (intérêts, principal, solde)."""
        if principal < 1e-6 or term_years <= 0 or annual_rate < 0:
             if principal < 1e-6 : print("DEBUG Loan Schedule: Principal nul ou quasi-nul.")
             if term_years <= 0 : print("DEBUG Loan Schedule: Durée nulle ou négative.")
             if annual_rate < 0 : print("DEBUG Loan Schedule: Taux annuel négatif.")
             # Retourner des zéros si pas de prêt ou paramètres invalides
             zeros = np.zeros(num_months_simulation)
             return zeros.copy(), zeros.copy(), zeros.copy()

        monthly_rate = annual_rate / 12.0
        n_payments = int(round(term_years * 12)) # Assurer un entier

        if abs(monthly_rate) < 1e-9: # Cas taux zéro
            monthly_payment = principal / n_payments if n_payments > 0 else 0
        else:
            try:
                # Formule classique de l'annuité constante
                factor = (1 + monthly_rate) ** n_payments
                denominator = factor - 1
                if abs(denominator) < 1e-12: # Éviter division par zéro
                     # Ceci arrive si factor est très proche de 1 (taux très proche de 0 et/ou durée très grande)
                     # Dans ce cas, on peut approximer par le cas taux zéro
                     print(f"AVERTISSEMENT Loan Schedule: Dénominateur annuité proche de zéro (factor={factor}). Approximation linéaire.")
                     monthly_payment = principal / n_payments if n_payments > 0 else 0
                else:
                     monthly_payment = principal * (monthly_rate * factor) / denominator
                     # Vérifier si le paiement est fini (peut être inf si factor est énorme)
                     if not np.isfinite(monthly_payment):
                          print(f"AVERTISSEMENT Loan Schedule: Paiement mensuel non fini ({monthly_payment}). Taux/durée trop élevés?")
                          monthly_payment = np.nan # Indiquer un problème
            except (OverflowError, ZeroDivisionError) as e:
                print(f"ERREUR Loan Schedule (Calcul Paiement): {e}. Taux/durée trop élevés?")
                monthly_payment = np.nan # Indiquer un problème

        # Gérer le cas où le calcul du paiement échoue
        if np.isnan(monthly_payment):
            print(f"ERREUR Loan Schedule: Échec calcul paiement mensuel. Retour de zéros.")
            zeros = np.zeros(num_months_simulation)
            return zeros.copy(), zeros.copy(), zeros.copy()


        interests = np.zeros(num_months_simulation)
        principals = np.zeros(num_months_simulation)
        balances = np.zeros(num_months_simulation)
        remaining_balance = principal

        for i in range(num_months_simulation):
            if i < n_payments and remaining_balance > 1e-6: # Tolérance pour solde quasi-nul
                interest_paid_this_month = remaining_balance * monthly_rate
                # Principal = Paiement - Intérêt, mais ne peut dépasser le solde restant
                principal_paid_this_month = min(monthly_payment - interest_paid_this_month, remaining_balance)
                # Assurer que le principal remboursé n'est pas négatif (peut arriver avec taux flottants)
                principal_paid_this_month = max(0, principal_paid_this_month)

                interests[i] = interest_paid_this_month
                principals[i] = principal_paid_this_month
                remaining_balance -= principal_paid_this_month
                # Assurer que le solde ne devient pas négatif à cause des erreurs flottantes
                remaining_balance = max(0, remaining_balance)
                balances[i] = remaining_balance
            else:
                # Prêt terminé ou jamais commencé
                interests[i] = 0.0
                principals[i] = 0.0
                # Le solde reste à 0 une fois le prêt terminé
                balances[i] = 0.0 if i >= n_payments else max(0, remaining_balance) # Gérer cas où simu > prêt

        return interests, principals, balances


    def calculate_payback_months(self, monthly_cash_flows):
        """Calcule le payback en mois à partir de flux mensuels (incluant T0)."""
        if not isinstance(monthly_cash_flows, np.ndarray):
            monthly_cash_flows = np.array(monthly_cash_flows)

        if len(monthly_cash_flows) == 0: return None # Pas de flux
        if monthly_cash_flows[0] >= -1e-9: return 0.0 # Payback immédiat (T0 >= 0)

        cumulative_cf = np.cumsum(monthly_cash_flows)
        # Trouver le premier index où le cumul devient >= 0
        positive_indices = np.where(cumulative_cf >= -1e-9)[0] # Tolérance pour zéro flottant

        if len(positive_indices) == 0:
            return None # Payback non atteint pendant la simulation

        # Index du premier mois où le cumul est >= 0
        # Note: l'index 0 correspond à T0, l'index 1 au Mois 1, etc.
        first_positive_idx = positive_indices[0]

        # Cas où ça devient positif pile à T0 (déjà géré au début)
        if first_positive_idx == 0: return 0.0

        # Mois précédent (index 0-based pour les flux)
        month_before_positive_idx = first_positive_idx - 1
        last_negative_cum_cf = cumulative_cf[month_before_positive_idx]
        # Flux du mois où le cumul traverse zéro
        cash_flow_crossing_month = monthly_cash_flows[first_positive_idx]

        # Calcul de la fraction du mois si le flux traversant est positif
        if cash_flow_crossing_month > 1e-9:
            fraction = -last_negative_cum_cf / cash_flow_crossing_month
            # S'assurer que la fraction est entre 0 et 1 (erreurs flottantes)
            fraction = max(0.0, min(1.0, fraction))
            # Payback = Nombre de mois complets AVANT le passage + fraction du mois de passage
            # Le nombre de mois complets avant est `first_positive_idx - 1`
            # (car l'index 1 est le 1er mois, donc l'index `k` est le k-ième mois)
            payback_months = (first_positive_idx - 1) + fraction
        # Cas où le cumul devient exactement zéro à la fin du mois `first_positive_idx`
        elif abs(cumulative_cf[first_positive_idx]) < 1e-9:
             # Le payback est atteint à la fin du mois `first_positive_idx` (numéro 1-based)
             payback_months = float(first_positive_idx)
        else:
            # Cas étrange : flux traversant nul ou négatif mais cumul devient positif ?
            # Peut arriver si T0 > 0 (géré au début) ou avec des flux erratiques.
            # Considérer le payback comme atteint à la fin du mois précédent.
             print(f"AVERTISSEMENT Payback: Flux traversant non positif ({cash_flow_crossing_month:.2f}) quand le cumul devient positif.")
             payback_months = float(first_positive_idx - 1) # Prudent

        return payback_months


    def calculate_lcoe_monthly(self, wacc_monthly, capex_net_subvention, monthly_df):
        """Calcule le LCOE à partir de données mensuelles."""
        # Vérifier validité WACC mensuel
        if wacc_monthly is None or wacc_monthly <= -1.0:
            print(f"AVERTISSEMENT LCOE: WACC mensuel invalide ({wacc_monthly}), LCOE non calculé.")
            return np.nan # Ou None

        try:
            # Coûts: CAPEX net T0 + OPEX mensuels + TURPE mensuels
            # Utiliser .get avec valeur par défaut 0 si colonne manque
            opex_monthly = monthly_df.get('OPEX', 0.0).fillna(0).values
            turpe_monthly = monthly_df.get('TURPE', 0.0).fillna(0).values
            operational_costs_monthly = opex_monthly + turpe_monthly

            # Flux de coûts pour NPV (T0 est négatif, les coûts opérationnels aussi)
            lcoe_cost_flows = np.concatenate(([-capex_net_subvention], -operational_costs_monthly))

            # Calculer NPV des coûts
            lcoe_discounted_costs_pv = npf.npv(wacc_monthly, lcoe_cost_flows)
            print(f"DEBUG LCOE HELPER: VAN Coûts (lcoe_discounted_costs_pv) = {lcoe_discounted_costs_pv}") # <-- AJOUT
            # Gérer si npv retourne NaN ou Inf
            if not np.isfinite(lcoe_discounted_costs_pv):
                 print(f"AVERTISSEMENT LCOE: NPV des coûts non finie ({lcoe_discounted_costs_pv}).")
                 return np.nan

            # Production mensuelle
            prod_monthly = monthly_df.get('Production_kWh', 0.0).fillna(0).values
            if len(prod_monthly) != len(operational_costs_monthly):
                 print("AVERTISSEMENT LCOE: Longueur Production et Coûts mensuels diffère.")
                 # Tenter d'ajuster si possible, ou retourner NaN
                 # Pour l'instant, on retourne NaN si les longueurs diffèrent
                 min_len = min(len(prod_monthly), len(operational_costs_monthly))
                 prod_monthly = prod_monthly[:min_len]
                 # Note: Cela suppose que les coûts après la fin de la prod ne comptent pas pour LCOE. Discutable.

            # Flux de production pour NPV (Pas de prod à T0)
            lcoe_prod_flows = np.concatenate(([0], prod_monthly))

            # Calculer NPV de la production
            lcoe_discounted_production_pv = npf.npv(wacc_monthly, lcoe_prod_flows)
            print(f"DEBUG LCOE HELPER: VAN Production (lcoe_discounted_production_pv) = {lcoe_discounted_production_pv}") # <-- AJOUT
            if not np.isfinite(lcoe_discounted_production_pv):
                 print(f"AVERTISSEMENT LCOE: NPV de la production non finie ({lcoe_discounted_production_pv}).")
                 return np.nan

            # Calculer LCOE : (Total coûts actualisés) / (Total production actualisée)
            # Le NPV des coûts est déjà négatif car flux = -coûts. Donc LCOE = -NPV(coûts) / NPV(prod)
            if abs(lcoe_discounted_production_pv) > 1e-9: # Modifié pour + de robustesse (était 1e-6)
                lcoe = -lcoe_discounted_costs_pv / lcoe_discounted_production_pv
                print(f"DEBUG LCOE HELPER: LCOE Calculé = {lcoe}") # <-- AJOUT
                return lcoe
            else:
                print("AVERTISSEMENT LCOE HELPER: Production actualisée nulle ou quasi-nulle.")
                return np.nan # Ou infini ? NaN est plus sûr.

        except Exception as e:
            print(f"ERREUR LCOE HELPER: {e}")
            # print(traceback.format_exc()) # Décommenter pour trace complète si besoin
            return np.nan # Ou None

    def calculate_avg_dscr_from_monthly(self, monthly_df):
        """Calcule le DSCR moyen à partir des données mensuelles."""
        if monthly_df.empty:
             print("AVERTISSEMENT DSCR: DataFrame mensuel vide.")
             return np.nan

        try:
            # Regrouper par année pour calculer DSCR annuel d'abord
            # S'assurer que l'index est bien de type Datetime
            if not isinstance(monthly_df.index, pd.DatetimeIndex):
                 print("AVERTISSEMENT DSCR: Index DataFrame mensuel n'est pas DatetimeIndex.")
                 # Essayer de convertir si possible
                 try:
                      monthly_df.index = pd.to_datetime(monthly_df.index)
                 except:
                      print("ERREUR DSCR: Impossible de convertir l'index en DatetimeIndex.")
                      return np.nan

            # Gérer les colonnes potentiellement manquantes avec .get
            # Utiliser fillna(0) au cas où des mois manqueraient dans une année
            annual_sum = monthly_df.groupby(monthly_df.index.year).agg(
                EBITDA_annuel=pd.NamedAgg(column='EBITDA', aggfunc=lambda x: x.fillna(0).sum()),
                # Utiliser l'impôt PROVISIONNÉ ici pour le flux dispo pour la dette
                Taxes_annuel=pd.NamedAgg(column='Impots_Provisionnes', aggfunc=lambda x: x.fillna(0).sum()),
                Interets_annuel=pd.NamedAgg(column='Interets_Payes', aggfunc=lambda x: x.fillna(0).sum()),
                Principal_annuel=pd.NamedAgg(column='Principal_Rembourse', aggfunc=lambda x: x.fillna(0).sum())
            )

            # Calculer Cash Available for DS (CADS) Annuel = EBITDA - Taxes (approximation)
            annual_sum['CADS_annuel'] = annual_sum['EBITDA_annuel'] - annual_sum['Taxes_annuel']
            # Calculer Service de Dette Annuel = Intérêts + Principal
            annual_sum['Debt_Service_annuel'] = annual_sum['Interets_annuel'] + annual_sum['Principal_annuel']

            # Calculer DSCR Annuel = CADS / Service Dette
            # Gérer la division par zéro (si pas de service de dette)
            annual_sum['DSCR_annuel'] = np.where(
                np.abs(annual_sum['Debt_Service_annuel']) > 1e-9, # Tolérance pour dette nulle
                annual_sum['CADS_annuel'] / annual_sum['Debt_Service_annuel'],
                np.inf # DSCR infini si pas de service de dette mais CADS > 0
            )
            # Si CADS <= 0 et Service Dette = 0, mettre NaN ? ou -Inf ? Mettons NaN.
            annual_sum.loc[(annual_sum['CADS_annuel'] <= 0) & (np.abs(annual_sum['Debt_Service_annuel']) <= 1e-9), 'DSCR_annuel'] = np.nan

            # Calculer la moyenne des DSCR annuels VALIDES (exclure Inf et NaN)
            valid_dscr = annual_sum['DSCR_annuel'][np.isfinite(annual_sum['DSCR_annuel'])]

            if not valid_dscr.empty:
                avg_dscr = valid_dscr.mean()
            # S'il n'y a que des infinis (pas de dette)
            elif not annual_sum['DSCR_annuel'][annual_sum['DSCR_annuel'] == np.inf].empty:
                avg_dscr = np.inf
            else: # Si aucune année valide (NaN ou vide)
                avg_dscr = np.nan

            return avg_dscr

        except Exception as e:
            print(f"ERREUR Calcul DSCR Moyen Mensuel: {e}")
            print(traceback.format_exc())
            return np.nan # Ou None


    # --- simulate_selling_price reste principalement inchangé ---
    # Mais il appellera maintenant la version MENSUELLE de calculate_financial_indicators
    def simulate_selling_price(self,
                               scenario_name: str,
                               target_irr: float | None = None,
                               target_npv: float | None = None,
                               override_source_prix_autoconso: str | None = None
                              ) -> dict | None:
        """
        Trouve le prix pour atteindre un TRI ou VAN cible, en utilisant les calculs MENSUELS.
        Utilise brentq pour VAN=0 si possible, sinon minimize.
        """
        print(f"MOTEUR (Mensuel): simulate_selling_price: scenario={scenario_name}, target_irr={target_irr}, target_npv={target_npv}, override_autoconso={override_source_prix_autoconso}")
        try:
            if target_irr is None and target_npv is None:
                raise ValueError("Veuillez spécifier un TRI ou une VAN cible")

            config = self.config
            prix_min_config = float(config.get('prix_min_revente', 0.05))
            prix_max_config = float(config.get('prix_max_revente', 0.40))
            if prix_min_config >= prix_max_config:
                 prix_min_config = 0.05; prix_max_config = 0.40
                 print(f"AVERTISSEMENT MOTEUR: Plage prix invalide, utilisation [{prix_min_config}, {prix_max_config}]")

            optimal_price = None

            # --- Fonction objectif simple pour la recherche de racine (retourne NPV) ---
            memoized_npv_results = {} # Cache simple pour éviter recalculs redondants lors de la recherche du bracket
            def npv_objective_for_root(price):
                price_rounded = round(price, 6) # Arrondir pour clé de cache
                if price_rounded in memoized_npv_results:
                    return memoized_npv_results[price_rounded]

                # Utiliser l'instance pour calculer les indicateurs (maintenant mensuels)
                results = self.calculate_financial_indicators( # Appelle la version mensuelle
                    scenario_name,
                    prix_revente=price,
                    override_source_prix_autoconso=override_source_prix_autoconso
                )
                if not results or not isinstance(results, dict) or results.get('npv') is None or not np.isfinite(results.get('npv')):
                    # Si le calcul échoue ou NPV invalide, on ne peut pas l'utiliser pour la racine
                    # Retourner une valeur qui n'aidera pas brentq (ou lever une erreur ?)
                    # Pour l'instant, retourner NaN pour indiquer un échec
                    print(f"AVERTISSEMENT ROOT: Calcul NPV échoué ou invalide pour prix {price:.6f}")
                    memoized_npv_results[price_rounded] = np.nan
                    return np.nan
                
                npv_value = results.get('npv')
                memoized_npv_results[price_rounded] = npv_value
                # --- AJOUT PRINT pour brentq ---
                print(f"DEBUG ROOT objective(price={price:.8f}) -> NPV={npv_value:.4f}")
                # --- FIN AJOUT ---
                return npv_value

            # --- TENTATIVE AVEC BRENTQ SI CIBLE = VAN 0 ---
            if target_npv is not None and abs(target_npv) < 1e-9:
                print("MOTEUR (Mensuel): Cible VAN=0 détectée. Tentative avec brentq...")
                memoized_npv_results.clear() # Vider le cache avant la recherche
                try:
                    # Évaluer aux bornes pour trouver un intervalle de changement de signe
                    npv_min = npv_objective_for_root(prix_min_config)
                    npv_max = npv_objective_for_root(prix_max_config)

                    # Vérifier si les NPVs sont valides et de signes opposés
                    if np.isfinite(npv_min) and np.isfinite(npv_max) and npv_min * npv_max < 0:
                        print(f"MOTEUR (Mensuel): Bracket trouvé [{prix_min_config:.4f}, {prix_max_config:.4f}] -> NPV [{npv_min:.2f}, {npv_max:.2f}]. Appel brentq...")
                        # Appel à brentq
                        optimal_price = brentq(npv_objective_for_root, prix_min_config, prix_max_config, xtol=1e-6, rtol=1e-6)
                        print(f"MOTEUR (Mensuel): brentq a convergé vers {optimal_price:.8f}")
                    else:
                        print(f"MOTEUR (Mensuel): Pas de changement de signe NPV trouvé aux bornes [{prix_min_config:.4f}, {prix_max_config:.4f}] (NPVs: [{npv_min:.2f}, {npv_max:.2f}]). Passage à minimize.")
                        # Si pas de changement de signe, brentq ne fonctionnera pas, on passera à minimize plus bas

                except ValueError as e_brentq: # Brentq peut lever ValueError si pas de changement de signe
                    print(f"MOTEUR (Mensuel): Erreur brentq (probablement pas de changement de signe ou échec convergence): {e_brentq}. Passage à minimize.")
                except Exception as e_root: # Autres erreurs potentielles
                     print(f"MOTEUR (Mensuel): Erreur pendant la recherche de racine avec brentq : {e_root}. Passage à minimize.")

            # --- SI BRENTQ N'A PAS ÉTÉ UTILISÉ OU A ÉCHOUÉ, OU SI CIBLE IRR ---
            # --- Utilisation de minimize comme avant (pour cible IRR ou fallback VAN=0) ---
            if optimal_price is None:
                print("MOTEUR (Mensuel): Utilisation de minimize (pour cible IRR ou fallback VAN=0).")
                iteration_count = 0
                objective_cache = {} # Cache simple pour l'objectif

                def objective_function_minimize(price_array):
                    nonlocal iteration_count
                    iteration_count += 1
                    price = float(price_array[0])
                    # price_rounded = round(price, 6) # <-- Cache désactivé

                    # --- AJOUT PRINT --- 
                    print(f"DEBUG MINIMIZE Iter {iteration_count}: Testing Price = {price:.8f}")
                    # --- FIN AJOUT --- 

                    # if price_rounded in objective_cache: # <-- Cache désactivé
                    #     print(f"  -> Minimize Cache Hit! Returning: {objective_cache[price_rounded]:.6e}") # <-- Cache désactivé
                    #     return objective_cache[price_rounded] # <-- Cache désactivé

                    results = self.calculate_financial_indicators( # Appelle la version mensuelle
                        scenario_name,
                        prix_revente=price,
                        override_source_prix_autoconso=override_source_prix_autoconso
                    )

                    if not results or not isinstance(results, dict):
                         # objective_cache[price_rounded] = 1e12 # <-- Cache désactivé
                         return 1e12

                    diff = 1e10
                    if target_irr is not None:
                        irr_value = results.get('irr')
                        if irr_value is not None and np.isfinite(irr_value):
                            target_irr_decimal = target_irr / 100.0 if abs(target_irr) > 1 else target_irr
                            diff = abs(irr_value - target_irr_decimal)**2 # Minimiser le carré de la différence peut aider
                        else: diff = 1e9
                    elif target_npv is not None: # Gère aussi le cas target_npv = 0 si brentq a échoué
                        npv_value = results.get('npv')
                        if npv_value is not None and np.isfinite(npv_value):
                            diff = abs(npv_value - target_npv)**2 # Minimiser le carré de la différence
                        else: diff = 1e9

                    # --- AJOUT PRINT --- 
                    target_display = target_irr if target_irr is not None else target_npv
                    type_cible = "IRR" if target_irr is not None else "NPV"
                    val_obtenue = results.get('irr') if target_irr is not None else results.get('npv')
                    val_obtenue_str = f"{val_obtenue:.6f}" if val_obtenue is not None else "N/A"
                    print(f"  -> Minimize Result: Target({type_cible})={target_display}, Got={val_obtenue_str}, Diff^2={diff:.6e}")
                    # --- FIN AJOUT --- 

                    # objective_cache[price_rounded] = diff # <-- Cache désactivé
                    return diff

                initial_price_guess = config.get('prix_vente_initial', (prix_min_config + prix_max_config) / 2)
                initial_price_guess = max(prix_min_config, min(prix_max_config, initial_price_guess))
                bounds = [(prix_min_config, prix_max_config)]

                result = minimize(objective_function_minimize, [initial_price_guess], method='L-BFGS-B', bounds=bounds,
                                  options={'ftol': 1e-9, 'gtol': 1e-7}) # Tolérances un peu plus strictes

                if result.success and bounds[0][0] <= result.x[0] <= bounds[0][1]:
                     optimal_price = result.x[0]
                else:
                    print(f"MOTEUR (Mensuel): L-BFGS-B échec/hors bornes (success={result.success}). Essai Nelder-Mead...")
                    def objective_wrapper_nelder(price_scalar):
                        if not (bounds[0][0] <= price_scalar <= bounds[0][1]): return 1e12
                        return objective_function_minimize([price_scalar])

                    result_nm = minimize(objective_wrapper_nelder, initial_price_guess, method='Nelder-Mead', options={'xatol': 1e-6, 'fatol': 1e-7})
                    if result_nm.success and bounds[0][0] <= result_nm.x[0] <= bounds[0][1]:
                        optimal_price = result_nm.x[0]
                    else:
                         print(f"MOTEUR (Mensuel): Nelder-Mead échec aussi (success={result_nm.success}).")
                         # Ne pas lever d'erreur ici si on veut quand même retourner le meilleur résultat trouvé, même s'il n'est pas parfait
                         # Garder le résultat du meilleur des deux essais, même si non optimal
                         if result.success and 'fun' in result and result.fun < result_nm.fun:
                              optimal_price = result.x[0]
                              print(f"AVERTISSEMENT MOTEUR: Convergence échouée, utilisation du résultat L-BFGS-B ({optimal_price:.6f}, diff^2={result.fun:.2e})")
                         elif result_nm.success and 'fun' in result_nm:
                              optimal_price = result_nm.x[0]
                              print(f"AVERTISSEMENT MOTEUR: Convergence échouée, utilisation du résultat Nelder-Mead ({optimal_price:.6f}, diff^2={result_nm.fun:.2e})")
                         else:
                             # Si les deux échouent complètement
                             raise RuntimeError("Convergence échouée par les deux méthodes pour trouver le prix cible (base mensuelle).")


            # --- Recalcul Final ---
            if optimal_price is None:
                # Ceci ne devrait pas arriver si on ne lève pas d'erreur en cas d'échec de minimize,
                # mais par sécurité:
                raise RuntimeError("Aucun prix optimal n'a pu être déterminé (base mensuelle).")

            # S'assurer que le prix optimal est dans les bornes (peut être légèrement dehors à cause des tolérances)
            optimal_price = max(prix_min_config, min(prix_max_config, optimal_price))

            print(f"MOTEUR (Mensuel): Recalcul final indicateurs avec prix optimal = {optimal_price:.8f}, override='{override_source_prix_autoconso}'")
            final_results = self.calculate_financial_indicators(
                scenario_name,
                prix_revente=optimal_price,
                override_source_prix_autoconso=override_source_prix_autoconso
            )

            if final_results and isinstance(final_results, dict):
                final_results['prix_revente_optimal_pour_cible'] = optimal_price
                final_results['target_irr_asked'] = target_irr
                final_results['target_npv_asked'] = target_npv
                final_results['lcoe_associated'] = final_results.get('lcoe')
                final_results['tarif_edf_reference'] = self.config.get('tarif_edf_reference')
                return final_results
            else:
                raise RuntimeError(f"Échec recalcul final indicateurs (base mensuelle) avec prix {optimal_price:.8f}")

        # --- Gestion Générale des Erreurs ---
        except (ValueError, TypeError, RuntimeError) as e:
            print(f"ERREUR MOTEUR (simulate_selling_price - Mensuel): {e}")
            raise e
        except Exception as e:
            print(f"ERREUR MOTEUR INATTENDUE (simulate_selling_price - Mensuel): {e}")
            traceback.print_exc()
            raise RuntimeError(f"Erreur inattendue lors de la simulation du prix (base mensuelle) : {e}") from e

    # --- Les autres méthodes (calculate_monthly_loan_schedule, etc.) restent ici ---
    # --- Assurez-vous que TOUTES les autres méthodes sont présentes ---
    # --- calculate_monthly_loan_schedule --- # Important : cette méthode doit rester !
    def calculate_monthly_loan_schedule(self, principal, annual_rate, term_years, num_months_simulation):
        """Calcule l'échéancier mensuel (intérêts, principal, solde)."""
        if principal < 1e-6 or term_years <= 0 or annual_rate < 0:
             if principal < 1e-6 : print("DEBUG Loan Schedule: Principal nul ou quasi-nul.")
             if term_years <= 0 : print("DEBUG Loan Schedule: Durée nulle ou négative.")
             if annual_rate < 0 : print("DEBUG Loan Schedule: Taux annuel négatif.")
             zeros = np.zeros(num_months_simulation)
             return zeros.copy(), zeros.copy(), zeros.copy()

        monthly_rate = annual_rate / 12.0
        n_payments = int(round(term_years * 12))

        if abs(monthly_rate) < 1e-9:
            monthly_payment = principal / n_payments if n_payments > 0 else 0
        else:
            try:
                factor = (1 + monthly_rate) ** n_payments
                denominator = factor - 1
                if abs(denominator) < 1e-12:
                     print(f"AVERTISSEMENT Loan Schedule: Dénominateur annuité proche de zéro (factor={factor}). Approximation linéaire.")
                     monthly_payment = principal / n_payments if n_payments > 0 else 0
                else:
                     monthly_payment = principal * (monthly_rate * factor) / denominator
                     if not np.isfinite(monthly_payment):
                          print(f"AVERTISSEMENT Loan Schedule: Paiement mensuel non fini ({monthly_payment}). Taux/durée trop élevés?")
                          monthly_payment = np.nan
            except (OverflowError, ZeroDivisionError) as e:
                print(f"ERREUR Loan Schedule (Calcul Paiement): {e}. Taux/durée trop élevés?")
                monthly_payment = np.nan

        if np.isnan(monthly_payment):
            print(f"ERREUR Loan Schedule: Échec calcul paiement mensuel. Retour de zéros.")
            zeros = np.zeros(num_months_simulation)
            return zeros.copy(), zeros.copy(), zeros.copy()

        interests = np.zeros(num_months_simulation)
        principals = np.zeros(num_months_simulation)
        balances = np.zeros(num_months_simulation)
        remaining_balance = principal

        for i in range(num_months_simulation):
            if i < n_payments and remaining_balance > 1e-6:
                interest_paid_this_month = remaining_balance * monthly_rate
                principal_paid_this_month = min(monthly_payment - interest_paid_this_month, remaining_balance)
                principal_paid_this_month = max(0, principal_paid_this_month)
                interests[i] = interest_paid_this_month
                principals[i] = principal_paid_this_month
                remaining_balance -= principal_paid_this_month
                remaining_balance = max(0, remaining_balance)
                balances[i] = remaining_balance
            else:
                interests[i] = 0.0
                principals[i] = 0.0
                balances[i] = 0.0 if i >= n_payments else max(0, remaining_balance)

        return interests, principals, balances

    # --- calculate_payback_months ---
    def calculate_payback_months(self, monthly_cash_flows):
        """Calcule le payback en mois à partir de flux mensuels (incluant T0)."""
        if not isinstance(monthly_cash_flows, np.ndarray):
            monthly_cash_flows = np.array(monthly_cash_flows)

        if len(monthly_cash_flows) == 0: return None # Pas de flux
        if monthly_cash_flows[0] >= -1e-9: return 0.0 # Payback immédiat (T0 >= 0)

        cumulative_cf = np.cumsum(monthly_cash_flows)
        positive_indices = np.where(cumulative_cf >= -1e-9)[0]

        if len(positive_indices) == 0:
            return None

        first_positive_idx = positive_indices[0]

        if first_positive_idx == 0: return 0.0

        month_before_positive_idx = first_positive_idx - 1
        last_negative_cum_cf = cumulative_cf[month_before_positive_idx]
        cash_flow_crossing_month = monthly_cash_flows[first_positive_idx]

        if cash_flow_crossing_month > 1e-9:
            fraction = -last_negative_cum_cf / cash_flow_crossing_month
            fraction = max(0.0, min(1.0, fraction))
            payback_months = (first_positive_idx - 1) + fraction
        elif abs(cumulative_cf[first_positive_idx]) < 1e-9:
             payback_months = float(first_positive_idx)
        else:
             print(f"AVERTISSEMENT Payback: Flux traversant non positif ({cash_flow_crossing_month:.2f}) quand le cumul devient positif.")
             payback_months = float(first_positive_idx - 1)

        return payback_months

    # --- calculate_lcoe_monthly ---
    def calculate_lcoe_monthly(self, wacc_monthly, capex_net_subvention, monthly_df):
        """Calcule le LCOE à partir de données mensuelles."""
        if wacc_monthly is None or wacc_monthly <= -1.0:
            print(f"AVERTISSEMENT LCOE: WACC mensuel invalide ({wacc_monthly}), LCOE non calculé.")
            return np.nan

        try:
            opex_monthly = monthly_df.get('OPEX', 0.0).fillna(0).values
            turpe_monthly = monthly_df.get('TURPE', 0.0).fillna(0).values
            operational_costs_monthly = opex_monthly + turpe_monthly
            lcoe_cost_flows = np.concatenate(([-capex_net_subvention], -operational_costs_monthly))
            lcoe_discounted_costs_pv = npf.npv(wacc_monthly, lcoe_cost_flows)
            print(f"DEBUG LCOE HELPER: VAN Coûts (lcoe_discounted_costs_pv) = {lcoe_discounted_costs_pv}")

            if not np.isfinite(lcoe_discounted_costs_pv):
                 print(f"AVERTISSEMENT LCOE: NPV des coûts non finie ({lcoe_discounted_costs_pv}).")
                 return np.nan

            prod_monthly = monthly_df.get('Production_kWh', 0.0).fillna(0).values
            if len(prod_monthly) != len(operational_costs_monthly):
                 print("AVERTISSEMENT LCOE: Longueur Production et Coûts mensuels diffère.")
                 min_len = min(len(prod_monthly), len(operational_costs_monthly))
                 prod_monthly = prod_monthly[:min_len]


            lcoe_prod_flows = np.concatenate(([0], prod_monthly))
            lcoe_discounted_production_pv = npf.npv(wacc_monthly, lcoe_prod_flows)
            print(f"DEBUG LCOE HELPER: VAN Production (lcoe_discounted_production_pv) = {lcoe_discounted_production_pv}")

            if not np.isfinite(lcoe_discounted_production_pv):
                 print(f"AVERTISSEMENT LCOE: NPV de la production non finie ({lcoe_discounted_production_pv}).")
                 return np.nan

            if abs(lcoe_discounted_production_pv) > 1e-9:
                lcoe = -lcoe_discounted_costs_pv / lcoe_discounted_production_pv
                print(f"DEBUG LCOE HELPER: LCOE Calculé = {lcoe}")
                return lcoe
            else:
                print("AVERTISSEMENT LCOE HELPER: Production actualisée nulle ou quasi-nulle.")
                return np.nan

        except Exception as e:
            print(f"ERREUR LCOE HELPER: {e}")
            return np.nan

    # --- calculate_avg_dscr_from_monthly ---
    def calculate_avg_dscr_from_monthly(self, monthly_df):
        """Calcule le DSCR moyen à partir des données mensuelles."""
        if monthly_df.empty:
             print("AVERTISSEMENT DSCR: DataFrame mensuel vide.")
             return np.nan

        try:
            if not isinstance(monthly_df.index, pd.DatetimeIndex):
                 print("AVERTISSEMENT DSCR: Index DataFrame mensuel n'est pas DatetimeIndex.")
                 try:
                      monthly_df.index = pd.to_datetime(monthly_df.index)
                 except:
                      print("ERREUR DSCR: Impossible de convertir l'index en DatetimeIndex.")
                      return np.nan

            annual_sum = monthly_df.groupby(monthly_df.index.year).agg(
                EBITDA_annuel=pd.NamedAgg(column='EBITDA', aggfunc=lambda x: x.fillna(0).sum()),
                Taxes_annuel=pd.NamedAgg(column='Impots_Provisionnes', aggfunc=lambda x: x.fillna(0).sum()),
                Interets_annuel=pd.NamedAgg(column='Interets_Payes', aggfunc=lambda x: x.fillna(0).sum()),
                Principal_annuel=pd.NamedAgg(column='Principal_Rembourse', aggfunc=lambda x: x.fillna(0).sum())
            )

            annual_sum['CADS_annuel'] = annual_sum['EBITDA_annuel'] - annual_sum['Taxes_annuel']
            annual_sum['Debt_Service_annuel'] = annual_sum['Interets_annuel'] + annual_sum['Principal_annuel']

            annual_sum['DSCR_annuel'] = np.where(
                np.abs(annual_sum['Debt_Service_annuel']) > 1e-9,
                annual_sum['CADS_annuel'] / annual_sum['Debt_Service_annuel'],
                np.inf
            )
            annual_sum.loc[(annual_sum['CADS_annuel'] <= 0) & (np.abs(annual_sum['Debt_Service_annuel']) <= 1e-9), 'DSCR_annuel'] = np.nan

            valid_dscr = annual_sum['DSCR_annuel'][np.isfinite(annual_sum['DSCR_annuel'])]

            if not valid_dscr.empty:
                avg_dscr = valid_dscr.mean()
            elif not annual_sum['DSCR_annuel'][annual_sum['DSCR_annuel'] == np.inf].empty:
                avg_dscr = np.inf
            else:
                avg_dscr = np.nan

            return avg_dscr

        except Exception as e:
            print(f"ERREUR Calcul DSCR Moyen Mensuel: {e}")
            print(traceback.format_exc())
            return np.nan

# --- Fin de la classe AnalysisEngine ---