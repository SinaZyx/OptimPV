import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from scipy.optimize import minimize
import time
from io import BytesIO
import io
import uuid
import xlsxwriter

# CORRECTION: Gestion de la dépendance à numpy_financial pour les fonctions irr et npv
try:
    import numpy_financial as npf
except ImportError:
    # Fonctions de secours si numpy_financial n'est pas disponible
    st.warning("Le package numpy_financial n'est pas installé. Utilisation de fonctions de secours pour IRR et NPV.")
    
    def secours_npv(rate, values):
        """Calcul manuel de la VAN si numpy_financial n'est pas disponible"""
        values = np.asarray(values)
        return (values / (1 + rate) ** np.arange(len(values))).sum()
    
    def secours_irr(values, guess=0.1):
        """Calcul manuel du TRI si numpy_financial n'est pas disponible"""
        def objective(rate):
            return secours_npv(rate, values)
        
        from scipy.optimize import newton
        try:
            # Utiliser la méthode de Newton pour trouver la racine
            return newton(objective, guess)
        except:
            # En cas d'échec, essayer avec différentes valeurs initiales
            try:
                return newton(objective, 0.05)
            except:
                try:
                    return newton(objective, 0.2)
                except:
                    return None
    
    # Créer un module fictif npf avec nos fonctions de secours
    class NpfModule:
        @staticmethod
        def npv(rate, values):
            return secours_npv(rate, values)
        
        @staticmethod
        def irr(values):
            return secours_irr(values)
    
    npf = NpfModule()

# --- CE BLOC EST COMMENTÉ CAR CES FONCTIONS SONT GÉRÉES PAR data_import.py ---
# # Définir les noms des colonnes attendues
# COLUMN_MAPPINGS = {
#     'date': 'Temps',
#     'production': 'Énergie PV (CA) déduction faite de la consommation en veille',
#     'consumption': 'Consommation'
# }
# 
# def validate_dataframe(df, column_mapping=None):
#     """
#     Valide que le DataFrame contient les colonnes nécessaires
#     
#     Args:
#         df: DataFrame à valider
#         column_mapping: Dictionnaire de mapping des colonnes (facultatif)
#         
#     Returns:
#         tuple: (bool, str) - (True si valide, message d'erreur si non valide)
#     """
#     if df is None:
#         return False, "Le DataFrame est vide"
#     
#     # Utiliser le mapping fourni ou le mapping par défaut
#     mapping = column_mapping or COLUMN_MAPPINGS
#     
#     # Vérifier que toutes les colonnes requises sont présentes
#     missing_columns = []
#     for key, expected_col in mapping.items():
#         if expected_col not in df.columns:
#             missing_columns.append(expected_col)
#     
#     if missing_columns:
#         return False, f"Colonnes manquantes : {', '.join(missing_columns)}"
#     
#     return True, "DataFrame valide"
# 
# def convert_date_format(date_str, year=None):
#     """
#     Convertit le format de date 'DD.MM. HH:mm' en datetime
#     
#     Args:
#         date_str: String de date au format 'DD.MM. HH:mm'
#         year: Année à utiliser (par défaut, année courante)
#         
#     Returns:
#         datetime: Date convertie
#     """
#     if year is None:
#         year = datetime.now().year
#         
#     try:
#         # Ajouter l'année et convertir en datetime
#         date_str = str(date_str).strip()
#         day, month = date_str.split('.')[0:2]
#         hour, minute = date_str.split(' ')[1].split(':')
#         
#         return datetime(year=year, 
#                        month=int(month) if month.strip() else 1,
#                        day=int(day),
#                        hour=int(hour),
#                        minute=int(minute))
#     except Exception as e:
#         st.error(f"Erreur lors de la conversion de la date '{date_str}': {str(e)}")
#         return None

class EconomicAnalysisModule:
    def __init__(self):
        # Initialiser les structures de données si elles n'existent pas
        if 'economic_results' not in st.session_state:
            st.session_state.economic_results = {}
    
    def calculate_wacc(self, debt_ratio, taux_interet_dette, taux_imposition, cout_fonds_propres):
        """
        Calcule le Coût Moyen Pondéré du Capital (WACC)
        
        Args:
            debt_ratio: Ratio de la dette (entre 0 et 1)
            taux_interet_dette: Taux d'intérêt de la dette en %
            taux_imposition: Taux d'imposition en %
            cout_fonds_propres: Coût des fonds propres en %
            
        Returns:
            float: WACC en décimal
        """
        # Coût de la dette après impôts
        cout_dette_apres_impots = (taux_interet_dette / 100) * (1 - taux_imposition / 100)
        
        # Ratio des fonds propres
        equity_ratio = 1 - debt_ratio
        
        # Calcul du WACC
        wacc = debt_ratio * cout_dette_apres_impots + equity_ratio * (cout_fonds_propres / 100)
        
        return wacc
    
    def preprocess_data(self, data):
        """
        Prétraite les données en convertissant les dates au bon format
        
        Args:
            data: DataFrame contenant les données brutes
            
        Returns:
            DataFrame: Données prétraitées ou None en cas d'erreur
        """
        try:
            # Copier les données pour ne pas modifier l'original
            processed_data = data.copy()
            
            # Vérifier que les colonnes requises existent
            required_columns = ['Temps', 'production_kwh', 'consumption_kwh']
            missing_columns = [col for col in required_columns if col not in processed_data.columns]
            
            if missing_columns:
                st.error(f"Colonnes manquantes dans les données : {', '.join(missing_columns)}")
                return None
            
            # CORRECTION: Vérifier si les données sont déjà dans le bon format
            # Vérifier si la colonne date est déjà en format datetime
            if not pd.api.types.is_datetime64_dtype(processed_data['Temps']):
                # Déterminer l'année à partir des données ou utiliser l'année courante
                try:
                    # Si l'année est déjà présente dans les données
                    first_date = processed_data['Temps'].iloc[0]
                    if isinstance(first_date, datetime):
                        year = first_date.year
                    else:
                        # Extraire l'année si possible
                        year = datetime.now().year
                except:
                    year = datetime.now().year
                
                # Convertir les dates
                processed_data['Temps'] = processed_data['Temps'].apply(
                    lambda x: convert_date_format(str(x), year) if pd.notnull(x) else None
                )
            
            # Supprimer les lignes avec des dates invalides
            processed_data = processed_data.dropna(subset=['Temps'])
            
            # Convertir les colonnes numériques
            for col in ['production_kwh', 'consumption_kwh']:
                processed_data[col] = pd.to_numeric(processed_data[col], errors='coerce')
            
            # Supprimer les lignes avec des valeurs manquantes
            processed_data = processed_data.dropna(subset=[
                'production_kwh',
                'consumption_kwh'
            ])
            
            return processed_data
            
        except Exception as e:
            st.error(f"Erreur lors du prétraitement des données : {str(e)}")
            return None
    
    def calculate_financial_indicators(self, scenario_name, prix_revente=None):
        """
        Calcule les indicateurs financiers pour un scénario donné
        
        Args:
            scenario_name: Nom du scénario à utiliser
            prix_revente: Prix de revente à utiliser (surcharge celui du scénario)
            
        Returns:
            dict: Dictionnaire contenant les indicateurs financiers calculés
        """
        try:
            if st.session_state.processed_data is None:
                st.error("Aucune donnée disponible. Veuillez importer des données avant de calculer les indicateurs.")
                return None
            
            # Obtenir les paramètres du scénario
            if scenario_name not in st.session_state.scenarios:
                st.error(f"Le scénario {scenario_name} n'existe pas.")
                return None
            
            scenario = st.session_state.scenarios[scenario_name]
            
            # Prétraiter les données si nécessaire
            data = st.session_state.processed_data.copy()
            
            # Obtenir les paramètres de configuration
            config = st.session_state.config
            
            # Paramètres de dette et d'équité - CORRECTION: utilisation des paramètres
            debt_ratio = config.get("debt_ratio", 0.80)  # Ratio dette avec valeur par défaut
            equity_ratio = 1 - debt_ratio
            
            # Durée du prêt - CORRECTION: utilisation des paramètres
            debt_term_years = config.get("debt_term_years", 15)  # Durée du prêt avec valeur par défaut
            
            # Prétraiter les données (s'assurer qu'elles sont au format horaire)
            # Extraire l'année de référence (année initiale du projet)
            reference_year = datetime.fromisoformat(config["date_debut_ppa"]).year
            
            # Ajouter une colonne pour l'année
            data['year'] = data['Temps'].dt.year
            
            # Ajouter une colonne pour le mois
            data['month'] = data['Temps'].dt.month
            
            # Ajouter une colonne pour le jour de l'année
            data['dayofyear'] = data['Temps'].dt.dayofyear
            
            # Ajouter une colonne pour l'heure
            data['hour'] = data['Temps'].dt.hour
            
            # Créer une clé unique pour chaque heure de l'année (jour de l'année * 24 + heure)
            data['hour_of_year'] = (data['dayofyear'] - 1) * 24 + data['hour']
            
            # Si l'année de référence se trouve dans les données, créer un profil de référence
            reference_data = None
            years_in_data = data['year'].unique()
            
            # CORRECTION: Meilleure détection des données de référence
            if reference_year in years_in_data:
                reference_data = data[data['year'] == reference_year].copy()
            else:
                # Utiliser la première année complète disponible comme référence
                complete_years = []
                for year in years_in_data:
                    hours_count = len(data[data['year'] == year])
                    # On assouplit le critère de "complétude" à 7000 heures (80% d'une année)
                    if hours_count >= 7000:  
                        complete_years.append(year)
                
                if complete_years:
                    reference_year = min(complete_years)
                    reference_data = data[data['year'] == reference_year].copy()
                    st.info(f"Utilisation de l'année {reference_year} comme année de référence avec {len(reference_data)} heures de données.")
                else:
                    # Si aucune année avec suffisamment de données n'est disponible, utiliser toutes les données
                    st.warning("Aucune année avec suffisamment de données n'est disponible. Les calculs utiliseront toutes les données disponibles, mais pourraient être imprécis.")
                    reference_data = data.copy()
            
            # Nombre d'années pour la simulation
            simulation_years = int(config["duree_ppa"] / 12)
            
            # Paramètres économiques
            taux_inflation = config["taux_inflation"] / 100  # Convertir en décimal
            taux_imposition = config["taux_imposition"] / 100  # Convertir en décimal
            prix_vente_initial = prix_revente if prix_revente is not None else config["prix_vente_initial"]
            capex = config["capex"] * scenario["capex_modifier"]
            opex_annual = config["opex"] * scenario["opex_modifier"]
            adjusted_inflation = taux_inflation * scenario["inflation_modifier"]
            
            # CORRECTION: Utilisation du taux de dégradation de la configuration
            degradation_rate = config["degradation_rate"] * scenario.get("degradation_modifier", 1.0)
            
            # Création des tableaux annuels
            years = np.arange(1, simulation_years + 1)
            revenues = np.zeros(simulation_years)
            opex = np.zeros(simulation_years)
            ebitda = np.zeros(simulation_years)
            debt_service = np.zeros(simulation_years)
            taxes = np.zeros(simulation_years)
            free_cash_flow = np.zeros(simulation_years)
            cumulative_cash_flow = np.zeros(simulation_years)
            dscr = np.zeros(simulation_years)
            annual_production = np.zeros(simulation_years)
            annual_consumption = np.zeros(simulation_years)
            annual_autoconsumption = np.zeros(simulation_years)
            annual_surplus = np.zeros(simulation_years)
            annual_deficit = np.zeros(simulation_years)
            
            # Tableaux pour le calcul précis des intérêts et du principal
            interest_paid = np.zeros(simulation_years)
            principal_paid = np.zeros(simulation_years)
            
            # Tableaux pour PVSOL (calcul parallèle)
            pvs_revenues_feedin = np.zeros(simulation_years)  # Revenus revente
            pvs_revenues_avoided = np.zeros(simulation_years) # Revenus économies (évités)
            pvs_opex = np.zeros(simulation_years)             # OPEX
            pvs_cash_flow = np.zeros(simulation_years)        # Cash flow annuel
            pvs_cumulative_cash_flow = np.zeros(simulation_years) # Cash flow cumulé
            
            # Paramètres PVSOL
            pvs_feed_in_tariff = config.get("pvs_feed_in_tariff", 0.1108)  # Tarif fixe
            pvs_avoided_cost_tariff = config.get("pvs_avoided_cost_tariff", 0.2218)  # Tarif initial évité
            
            # Créer un DataFrame pour stocker les profils de production et consommation pour chaque année
            yearly_profiles = {}
            
            # Pour chaque année de la simulation, créer un profil basé sur les données de référence
            for year in range(1, simulation_years + 1):
                # CORRECTION: Nouveau calcul du facteur de dégradation utilisant le taux configuré
                degradation_factor = (1 - degradation_rate) ** (year - 1)
                
                # Copier les données de référence
                year_data = reference_data.copy()
                
                # Appliquer le facteur de dégradation à la production
                year_data['production_kwh'] = year_data['production_kwh'] * degradation_factor * scenario["production_modifier"]
                
                # Stocker le profil annuel
                yearly_profiles[year] = year_data
                
                # Calculer les métriques énergétiques pour cette année
                total_production = year_data['production_kwh'].sum()
                total_consumption = year_data['consumption_kwh'].sum()
                
                # Calculer l'autoconsommation et le surplus HEURE PAR HEURE
                year_data['autoconsumption'] = year_data.apply(
                    lambda row: min(row['production_kwh'], row['consumption_kwh']), 
                    axis=1
                )
                
                year_data['surplus'] = year_data['production_kwh'] - year_data['autoconsumption']
                year_data['deficit'] = year_data['consumption_kwh'] - year_data['autoconsumption']
                
                # Calculer les totaux annuels
                annual_production[year-1] = total_production
                annual_consumption[year-1] = total_consumption
                annual_autoconsumption[year-1] = year_data['autoconsumption'].sum()
                annual_surplus[year-1] = year_data['surplus'].sum()
                annual_deficit[year-1] = year_data['deficit'].sum()
                
                # Calculer le prix de vente pour cette année (avec inflation)
                prix_vente_year = prix_vente_initial * (1 + adjusted_inflation) ** (year - 1)
                
                # Calculer les revenus en tenant compte de l'autoconsommation et du surplus
                # Valoriser l'autoconsommation au prix d'achat évité (qui peut être différent du prix de vente)
                # Pour simplifier, on suppose que le prix d'achat évité est le même que le prix de vente
                prix_achat_evite = prix_vente_initial * (1 + adjusted_inflation) ** (year - 1)
                
                # Calculer les revenus totaux pour cette année
                revenus_autoconsommation = annual_autoconsumption[year-1] * prix_achat_evite
                revenus_surplus = annual_surplus[year-1] * prix_vente_year
                revenues[year-1] = revenus_autoconsommation + revenus_surplus
                
                # Calculer l'OPEX pour cette année (avec inflation)
                opex[year-1] = opex_annual * (1 + adjusted_inflation) ** (year - 1)
                
                # PVSOL: Calcul des revenus selon leur méthode
                # Revenus de revente: tarif fixe * surplus
                pvs_revenues_feedin[year-1] = annual_surplus[year-1] * pvs_feed_in_tariff
                
                # Revenus économies: tarif évité (avec inflation) * autoconsommation
                pvs_avoided_tariff_year = pvs_avoided_cost_tariff * (1 + taux_inflation) ** (year - 1)
                pvs_revenues_avoided[year-1] = annual_autoconsumption[year-1] * pvs_avoided_tariff_year
                
                # OPEX PVSOL (avec inflation)
                pvs_opex[year-1] = opex_annual * (1 + taux_inflation) ** (year - 1)
            
            # Calculer l'EBITDA pour chaque année
            ebitda = revenues - opex
            
            # CORRECTION: Utiliser les paramètres de ratio dette/fonds propres
            debt_amount = capex * debt_ratio
            equity_amount = capex * equity_ratio
            
            # Paramètres du financement
            # --- DÉBUT DU BLOC CORRIGÉ ---
            # Vérifier si un prêt est actif et lire le taux d'intérêt de manière sécurisée
            loan_active = config.get("with_loan", True) # Prend True par défaut si la clé manque
            taux_interet_dette_pct = config.get("taux_interet_dette", 0.0) if loan_active else 0.0 # 0.0% si pas de prêt
            taux_interet_dette = taux_interet_dette_pct / 100 # Taux en décimal (sera 0.0 si pas de prêt)

            # Assurez-vous aussi que debt_ratio est 0 si pas de prêt (cohérence pour WACC etc.)
            debt_ratio = config.get("debt_ratio", 0.80) if loan_active else 0.0
            equity_ratio = 1 - debt_ratio 

            # Recalculer les montants avec les ratios potentiellement ajustés (car debt_ratio a pu changer)
            debt_amount = capex * debt_ratio
            equity_amount = capex * equity_ratio
            # --- FIN DU BLOC CORRIGÉ ---
            
            # Recalculer les montants avec les ratios potentiellement ajustés
            debt_amount = capex * debt_ratio
            equity_amount = capex * equity_ratio
            
            # CORRECTION: Calcul de l'annuité avec gestion des cas limites
            if taux_interet_dette < 0.0001:  # Cas particulier: taux proche de zéro
                annual_debt_payment = debt_amount / debt_term_years
            else:
                # Formule de l'annuité: A = P * r * (1 + r)^n / ((1 + r)^n - 1)
                annual_debt_payment = debt_amount * taux_interet_dette * (1 + taux_interet_dette) ** debt_term_years / ((1 + taux_interet_dette) ** debt_term_years - 1)
            
            # Établir le tableau d'amortissement
            remaining_debt = debt_amount
            for i in range(simulation_years):
                year = i + 1
                if year <= debt_term_years:
                    # Calculer les intérêts payés cette année
                    interest_paid[i] = remaining_debt * taux_interet_dette
                    
                    # Le remboursement du principal est la différence entre le paiement total et les intérêts
                    principal_this_year = min(annual_debt_payment - interest_paid[i], remaining_debt)
                    principal_paid[i] = principal_this_year
                    
                    # Mise à jour de la dette restante
                    remaining_debt -= principal_this_year
                    
                    # Paiement total du service de la dette
                    debt_service[i] = interest_paid[i] + principal_paid[i]
                else:
                    # Après la fin du prêt, il n'y a plus de service de la dette
                    interest_paid[i] = 0
                    principal_paid[i] = 0
                    debt_service[i] = 0
            
            # Calculer les impôts pour chaque année
            for i in range(simulation_years):
                # Le revenu imposable est l'EBITDA moins les intérêts payés
                taxable_income = ebitda[i] - interest_paid[i]
                
                # Les impôts ne sont payés que sur les revenus positifs
                taxes[i] = max(0, taxable_income * taux_imposition)
            
            # Calculer le free cash flow pour chaque année (Cash Flow to Equity - CFE)
            # CFE = EBITDA - Intérêts - Impôts - Remboursement du Principal
            for i in range(simulation_years):
                free_cash_flow[i] = ebitda[i] - interest_paid[i] - taxes[i] - principal_paid[i]
            
            # Calculer le cash flow cumulé
            # Première année: cash flow - investissement initial en fonds propres
            cumulative_cash_flow[0] = free_cash_flow[0] - equity_amount
            
            # Années suivantes: ajouter le cash flow de l'année au cumulé précédent
            for i in range(1, simulation_years):
                cumulative_cash_flow[i] = cumulative_cash_flow[i-1] + free_cash_flow[i]
            
            # PVSOL: Calculer le cash flow annuel et cumulé
            # Première année: Revenus - OPEX - CAPEX
            pvs_cash_flow[0] = (pvs_revenues_feedin[0] + pvs_revenues_avoided[0] - pvs_opex[0]) - capex
            pvs_cumulative_cash_flow[0] = pvs_cash_flow[0]
            
            # Années suivantes
            for i in range(1, simulation_years):
                pvs_cash_flow[i] = pvs_revenues_feedin[i] + pvs_revenues_avoided[i] - pvs_opex[i]
                pvs_cumulative_cash_flow[i] = pvs_cumulative_cash_flow[i-1] + pvs_cash_flow[i]
            
            # Calculer le DSCR pour chaque année
            for i in range(simulation_years):
                if debt_service[i] > 0:
                    # Calculer le Cash Flow Available for Debt Service (CFADS)
                    cfads = ebitda[i] - taxes[i]
                    dscr[i] = cfads / debt_service[i]
                else:
                    dscr[i] = float('inf')  # Pas de service de la dette à couvrir
            
            # Calculer le TRI (IRR)
            # Le flux initial est -equity_amount (investissement en fonds propres)
            cash_flows = [-equity_amount] + list(free_cash_flow)
            try:
                # CORRECTION: Utilisation de npf.irr au lieu de np.irr
                irr = npf.irr(cash_flows)
            except:
                st.warning("Impossible de calculer le TRI. Vérifiez que les flux de trésorerie sont cohérents.")
                irr = None
            
            # CORRECTION: Calcul du WACC et utilisation pour la VAN
            cout_fonds_propres = config.get("cout_fonds_propres", 8.0)  # Valeur par défaut: 8%
            wacc = self.calculate_wacc(debt_ratio, taux_interet_dette_pct, config["taux_imposition"], cout_fonds_propres)
            
            # Calculer la VAN (NPV) en utilisant le WACC comme taux d'actualisation
            # CORRECTION: Utilisation de npf.npv au lieu de np.npv
            npv = npf.npv(wacc, cash_flows)
            
            # CORRECTION: Calcul plus précis du ROI en prenant en compte la valeur temporelle de l'argent
            # ROI = (VAN + investissement initial) / investissement initial
            roi = (npv + equity_amount) / equity_amount
            
            # Calculer la période de récupération (Payback Period)
            payback_period = float('inf')  # Valeur par défaut: infini
            for i in range(simulation_years):
                if cumulative_cash_flow[i] >= 0:
                    # Interpolation linéaire pour une estimation plus précise
                    if i > 0 and cumulative_cash_flow[i-1] < 0:
                        fraction = -cumulative_cash_flow[i-1] / (cumulative_cash_flow[i] - cumulative_cash_flow[i-1])
                        payback_period = i + fraction
                    else:
                        payback_period = i + 1
                    break
            
            # Calculer le DSCR moyen sur la durée du prêt
            avg_dscr = np.mean(dscr[:debt_term_years]) if debt_term_years <= simulation_years else np.mean(dscr)
            
            # CORRECTION: Calcul standardisé et cohérent du taux d'autoconsommation
            autoconsumption_rate = 0.0
            if annual_production.sum() > 0:
                autoconsumption_rate = annual_autoconsumption.sum() / annual_production.sum()
            
            # CORRECTION: Calcul standardisé et cohérent du taux d'autoproduction
            autoproduction_rate = 0.0
            if annual_consumption.sum() > 0:
                autoproduction_rate = annual_autoconsumption.sum() / annual_consumption.sum()
            
            # Construire le dictionnaire de résultats
            results = {
                "scenario": scenario_name,
                "prix_revente": prix_vente_initial,
                "capex": capex,
                "equity_amount": equity_amount,
                "debt_amount": debt_amount,
                "annual_production": annual_production,
                "annual_consumption": annual_consumption,
                "annual_autoconsumption": annual_autoconsumption,
                "annual_surplus": annual_surplus,
                "annual_deficit": annual_deficit,
                "autoconsumption_rate": autoconsumption_rate,
                "autoproduction_rate": autoproduction_rate,
                "revenues": revenues,
                "opex": opex,
                "ebitda": ebitda,
                "debt_service": debt_service,
                "interest_paid": interest_paid,
                "principal_paid": principal_paid,
                "taxes": taxes,
                "free_cash_flow": free_cash_flow,
                "cumulative_cash_flow": cumulative_cash_flow,
                "dscr": dscr,
                "avg_dscr": avg_dscr,
                "irr": irr,
                "wacc": wacc,  # CORRECTION: Ajout du WACC aux résultats
                "npv": npv,
                "roi": roi,
                "payback_period": payback_period,
                "years": years,
                # Ajouter les résultats PVSOL
                "pvs_revenues_feedin": pvs_revenues_feedin,
                "pvs_revenues_avoided": pvs_revenues_avoided,
                "pvs_opex": pvs_opex,
                "pvs_cash_flow": pvs_cash_flow,
                "pvs_cumulative_cash_flow": pvs_cumulative_cash_flow,
                # CORRECTION: Ajouter les paramètres de financement utilisés
                "debt_ratio": debt_ratio,
                "equity_ratio": equity_ratio,
                "debt_term_years": debt_term_years,
                "degradation_rate": degradation_rate,
                # Ajouter la ligne pour les cash flows
                "cash_flows_for_irr_npv": cash_flows  # Ajout pour export formules
            }
            
            return results
        
        except Exception as e:
            st.error(f"Erreur lors du calcul des indicateurs financiers : {str(e)}")
            import traceback
            st.error(traceback.format_exc())
            return None
    
    def simulate_selling_price(self, scenario_name, target_irr=None, target_npv=None):
        """
        Simule différents prix de revente pour atteindre un TRI ou une VAN cible
        
        Args:
            scenario_name: Nom du scénario à simuler
            target_irr: TRI cible (en pourcentage)
            target_npv: VAN cible (en euros)
            
        Returns:
            dict: Résultats de la simulation avec le prix de revente optimal
        """
        if target_irr is None and target_npv is None:
            st.error("Veuillez spécifier soit un TRI cible, soit une VAN cible.")
            return None
            
        if target_irr is not None and target_npv is not None:
            st.warning("Veuillez spécifier soit un TRI cible, soit une VAN cible, mais pas les deux.")
            return None
            
        # Fonction objectif pour l'optimisation
        def objective(prix_revente):
            results = self.calculate_financial_indicators(scenario_name, prix_revente[0])
            if results is None:
                return float('inf')
                
            if target_irr is not None:
                if results['irr'] is None:
                    return float('inf')
                return abs(results['irr'] * 100 - target_irr)
            else:
                return abs(results['npv'] - target_npv)
        
        # Bornes pour le prix de revente (entre 0 et 1 €/kWh)
        bounds = [(0, 1)]
        
        # Point de départ : prix de revente actuel
        x0 = [st.session_state.config['prix_vente_initial']]
        
        # Optimisation
        result = minimize(objective, x0, bounds=bounds, method='Nelder-Mead')
        
        if not result.success:
            st.error("L'optimisation n'a pas convergé. Impossible de trouver un prix de revente optimal.")
            return None
            
        # Calculer les indicateurs avec le prix optimal
        prix_optimal = result.x[0]
        results = self.calculate_financial_indicators(scenario_name, prix_optimal)
        
        if results is None:
            st.error("Erreur lors du calcul des indicateurs avec le prix optimal.")
            return None
            
        # Ajouter le prix optimal aux résultats
        results['prix_revente_optimal'] = prix_optimal
        results['target_irr'] = target_irr
        results['target_npv'] = target_npv
        
        return results
    
    def compare_scenarios(self, scenario_names):
        """
        Compare les indicateurs financiers pour plusieurs scénarios
        
        Args:
            scenario_names: Liste des noms de scénarios à comparer
            
        Returns:
            dict: Dictionnaire contenant les comparaisons
        """
        results = {}
        
        for scenario_name in scenario_names:
            results[scenario_name] = self.calculate_financial_indicators(scenario_name)
        
        return results
    
    def sensitivity_analysis(self, scenario_name, parameter, values):
        """
        Réalise une analyse de sensibilité sur un paramètre donné
        
        Args:
            scenario_name: Nom du scénario de base
            parameter: Paramètre à faire varier
            values: Liste des valeurs à tester
            
        Returns:
            dict: Dictionnaire contenant les résultats pour chaque valeur
        """
        results = {}
        
        # Créer une copie locale de la configuration
        config_locale = dict(st.session_state.config)
        
        # Sauvegarder la configuration originale
        config_original = st.session_state.config
        
        try:
            # Pour chaque valeur à tester
            for value in values:
                # Modifier la configuration locale
                if parameter == 'prix_revente':
                    config_locale['prix_vente_initial'] = value
                elif parameter == 'inflation':
                    config_locale['taux_inflation'] = value
                elif parameter == 'opex':
                    config_locale['opex'] = value
                elif parameter == 'capex':
                    config_locale['capex'] = value
                # CORRECTION: Ajouter d'autres paramètres testables
                elif parameter == 'debt_ratio':
                    config_locale['debt_ratio'] = value
                elif parameter == 'debt_term_years':
                    config_locale['debt_term_years'] = value
                elif parameter == 'degradation_rate':
                    config_locale['degradation_rate'] = value
                else:
                    st.error(f"Paramètre inconnu : {parameter}")
                    return None
                
                # Utiliser temporairement la configuration locale
                st.session_state.config = config_locale
                
                # Calculer les indicateurs
                results[value] = self.calculate_financial_indicators(scenario_name)
            
            return results
        finally:
            # Restaurer la configuration originale
            st.session_state.config = config_original
    
    def show_ui(self):
        """Affiche l'interface utilisateur du module d'analyse économique"""
        st.markdown("<h1 class='main-header'>Analyse Économique</h1>", unsafe_allow_html=True)
        
        # Vérifier que les données nécessaires sont disponibles
        if not st.session_state.data_imported:
            st.warning("Aucune donnée n'a été importée. Veuillez d'abord importer des données dans l'onglet 'Importation Données'.")
            return
        
        # Créer des onglets pour les différentes analyses
        tab1, tab2, tab3, tab4 = st.tabs(["Analyse de Base", "Comparaison des Scénarios", "Analyse de Sensibilité", "Simulation du Prix de Revente"])
        
        with tab1:
            st.markdown("<h3 class='sub-header'>Analyse Économique de Base</h3>", unsafe_allow_html=True)
            
            # Paramètres financiers supplémentaires
            with st.expander("Paramètres financiers avancés"):
                col1, col2 = st.columns(2)
                with col1:
                    # CORRECTION: Ajout des paramètres manquants à l'interface
                    debt_ratio = st.slider(
                        "Ratio Dette/Total (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(st.session_state.config.get("debt_ratio", 0.80) * 100),
                        step=1.0,
                        key="debt_ratio_slider"
                    ) / 100.0
                    st.session_state.config["debt_ratio"] = debt_ratio
                
                with col2:
                    debt_term_years = st.number_input(
                        "Durée du prêt (années)",
                        min_value=1,
                        max_value=30,
                        value=int(st.session_state.config.get("debt_term_years", 15)),
                        step=1,
                        key="debt_term_years_input"
                    )
                    st.session_state.config["debt_term_years"] = debt_term_years
            
            # Sélectionner le scénario à analyser
            scenario = st.selectbox(
                "Sélectionnez un scénario",
                options=list(st.session_state.scenarios.keys()),
                index=0,
                key="basic_analysis_scenario"
            )
            
            # Bouton pour calculer les indicateurs
            if st.button("Calculer les indicateurs financiers", key="calc_basic"):
                with st.spinner("Calcul des indicateurs financiers en cours..."):
                    # Calculer les indicateurs
                    results = self.calculate_financial_indicators(scenario)
                    
                    if results:
                        # Stocker les résultats dans la session
                        st.session_state.economic_results[scenario] = results
                        
                        # Afficher les résultats
                        self.display_financial_results(results, key_prefix="basic_")
            
            # Si des résultats existent déjà pour ce scénario, les afficher
            if scenario in st.session_state.economic_results:
                self.display_financial_results(st.session_state.economic_results[scenario], key_prefix="basic_")
        
        with tab2:
            st.markdown("<h3 class='sub-header'>Comparaison des Scénarios</h3>", unsafe_allow_html=True)
            
            # Sélectionner les scénarios à comparer
            scenarios_to_compare = st.multiselect(
                "Sélectionnez les scénarios à comparer",
                options=list(st.session_state.scenarios.keys()),
                default=list(st.session_state.scenarios.keys())[:2] if len(st.session_state.scenarios) >= 2 else list(st.session_state.scenarios.keys()),
                key="compare_scenarios"
            )
            
            # Bouton pour calculer la comparaison
            if st.button("Comparer les scénarios", key="calc_compare") and scenarios_to_compare:
                with st.spinner("Comparaison des scénarios en cours..."):
                    # Calculer les indicateurs pour chaque scénario
                    results = self.compare_scenarios(scenarios_to_compare)
                    
                    if results:
                        # Stocker les résultats dans la session
                        for scenario, result in results.items():
                            st.session_state.economic_results[scenario] = result
                        
                        # Afficher la comparaison
                        self.display_scenarios_comparison(results)
            
            # Si des résultats existent déjà pour tous les scénarios sélectionnés, afficher la comparaison
            if all(scenario in st.session_state.economic_results for scenario in scenarios_to_compare) and scenarios_to_compare:
                results = {scenario: st.session_state.economic_results[scenario] for scenario in scenarios_to_compare}
                self.display_scenarios_comparison(results)
        
        with tab3:
            st.markdown("<h3 class='sub-header'>Analyse de Sensibilité</h3>", unsafe_allow_html=True)
            
            # Sélectionner le scénario de base
            base_scenario = st.selectbox(
                "Sélectionnez un scénario de base",
                options=list(st.session_state.scenarios.keys()),
                index=0,
                key="sensitivity_base_scenario"
            )
            
            # Sélectionner le paramètre à faire varier
            parameter = st.selectbox(
                "Sélectionnez le paramètre à faire varier",
                options=["prix_revente", "inflation", "opex", "capex", "debt_ratio", "debt_term_years", "degradation_rate"],
                format_func=lambda x: {
                    "prix_revente": "Prix de revente (€/kWh)",
                    "inflation": "Taux d'inflation (%)",
                    "opex": "OPEX (€/an)",
                    "capex": "CAPEX (€)",
                    "debt_ratio": "Ratio Dette/Total",
                    "debt_term_years": "Durée du prêt (années)",
                    "degradation_rate": "Taux de dégradation annuel (%)"
                }[x],
                key="sensitivity_parameter"
            )
            
            # Définir les valeurs à tester
            if parameter == "prix_revente":
                min_val = 0.05
                max_val = 0.25
                step = 0.01
                default_min = 0.10
                default_max = 0.20
                unit = "€/kWh"
                n_values = 11
            elif parameter == "inflation":
                min_val = 0.0
                max_val = 5.0
                step = 0.1
                default_min = 1.0
                default_max = 3.0
                unit = "%"
                n_values = 21
            elif parameter == "opex":
                min_val = 500
                max_val = 10000
                step = 500
                default_min = 3000
                default_max = 6000
                unit = "€/an"
                n_values = 5
            elif parameter == "capex":
                min_val = 50000
                max_val = 150000
                step = 10000
                default_min = 70000
                default_max = 100000
                unit = "€"
                n_values = 11
            # CORRECTION: Ajout des nouveaux paramètres
            elif parameter == "debt_ratio":
                min_val = 0.5
                max_val = 0.9
                step = 0.05
                default_min = 0.7
                default_max = 0.85
                unit = ""
                n_values = 7
            elif parameter == "debt_term_years":
                min_val = 10
                max_val = 25
                step = 1
                default_min = 12
                default_max = 20
                unit = "années"
                n_values = 9
            elif parameter == "degradation_rate":
                min_val = 0.001
                max_val = 0.01
                step = 0.001
                default_min = 0.003
                default_max = 0.007
                unit = ""
                n_values = 5
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_value = st.number_input(
                    f"Valeur minimale ({unit})",
                    min_value=float(min_val),
                    max_value=float(max_val),
                    value=float(default_min),
                    step=float(step),
                    key="sensitivity_min"
                )
            
            with col2:
                max_value = st.number_input(
                    f"Valeur maximale ({unit})",
                    min_value=float(min_val),
                    max_value=float(max_val),
                    value=float(default_max),
                    step=float(step),
                    key="sensitivity_max"
                )
            
            # Générer les valeurs à tester
            values = np.linspace(min_value, max_value, n_values)
            
            # Bouton pour calculer l'analyse de sensibilité
            if st.button("Calculer l'analyse de sensibilité", key="calc_sensitivity"):
                with st.spinner("Analyse de sensibilité en cours..."):
                    # Réaliser l'analyse de sensibilité
                    results = self.sensitivity_analysis(base_scenario, parameter, values)
                    
                    if results:
                        # Afficher les résultats
                        self.display_sensitivity_analysis(results, parameter, unit)
        
        with tab4:
            st.markdown("<h3 class='sub-header'>Simulation du Prix de Revente</h3>", unsafe_allow_html=True)
            
            # Sélectionner le scénario à analyser
            scenario_for_simulation = st.selectbox(
                "Sélectionnez un scénario",
                options=list(st.session_state.scenarios.keys()),
                index=0,
                key="selling_price_scenario"
            )
            
            # Demander le TRI ou la VAN cible
            target_type = st.radio("Objectif de simulation", ["TRI Cible", "VAN Cible"], key="target_type")
            
            if target_type == "TRI Cible":
                target_irr = st.number_input("TRI Cible (%)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, key="target_irr_value")
                target_npv = None
            else:
                target_irr = None
                target_npv = st.number_input("VAN Cible (€)", min_value=-1000000.0, max_value=10000000.0, value=0.0, step=10000.0, key="target_npv_value")
            
            # Bouton pour simuler
            if st.button("Simuler pour atteindre l'objectif", key="calc_selling_price"):
                with st.spinner("Simulation en cours..."):
                    # Simuler avec le prix de revente
                    results = self.simulate_selling_price(scenario_for_simulation, target_irr=target_irr, target_npv=target_npv)
                    
                    if results:
                        # Afficher les résultats
                        self.display_financial_results(results, key_prefix="simulation_")
                        
                        # Afficher un message sur la rentabilité
                        self.assess_profitability(results)
    
    def display_financial_results(self, results, key_prefix=""):
        """
        Affiche les résultats financiers d'un scénario de façon centralisée
        
        Args:
            results: Dictionnaire contenant les résultats financiers
            key_prefix: Préfixe pour rendre les clés Streamlit uniques
        """
        # Récupérer le nom du scénario pour créer des clés uniques
        scenario_name = results['scenario']
        
        # Générer un ID unique pour éviter les conflits de clés
        unique_id = int(time.time() * 1000) % 10000
        
        st.markdown("### Résultats de l'Analyse Financière")
        
        # Utiliser des métriques Streamlit au lieu du HTML personnalisé
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Rentabilité**")
            st.metric("ROI", f"{results['roi']*100:.2f}%")
            
            irr_value = f"{results['irr']*100:.2f}%" if results['irr'] is not None else "N/A"
            st.metric("TRI (IRR)", irr_value)
        
        with col2:
            st.markdown("**Viabilité**")
            st.metric("DSCR moyen", f"{results['avg_dscr']:.2f}")
            
            payback_value = f"{results['payback_period']:.2f} ans" if results['payback_period'] != float('inf') else "N/A"
            st.metric("Retour sur investissement", payback_value)
        
        with col3:
            st.markdown("**Performance**")
            st.metric("VAN (NPV)", f"{results['npv']:,.0f} €")
            st.metric("Prix de revente", f"{results['prix_revente']:.4f} €/kWh")
        
        # Paramètres financiers en expandable section
        with st.expander("Détails des paramètres financiers"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Ratio Dette/Total", f"{results['debt_ratio']*100:.1f}%")
                st.metric("CAPEX", f"{results['capex']:,.2f} €")
            
            with col2:
                st.metric("Durée du prêt", f"{results['debt_term_years']} ans")
                st.metric("Dette", f"{results['debt_amount']:,.2f} €")
            
            with col3:
                st.metric("Fonds propres", f"{results['equity_amount']:,.2f} €")
                st.metric("WACC", f"{results['wacc']*100:.2f}%")
            
            with col4:
                st.metric("Taux Dégradation", f"{results['degradation_rate']*100:.2f}% par an")
                st.metric("Autoconsommation", f"{results['autoconsumption_rate']*100:.2f}%")
        
        # Créer un DataFrame pour faciliter la création de graphiques
        df_financial = pd.DataFrame({
            "Année": results['years'],
            "Revenus": results['revenues'],
            "OPEX": results['opex'],
            "EBITDA": results['ebitda'],
            "Service de la Dette": results['debt_service'],
            "Free Cash Flow": results['free_cash_flow'],
            "Flux Cumulé": results['cumulative_cash_flow'],
            "DSCR": results['dscr']
        })
        
        # Option de filtrage par année
        années_min = int(df_financial['Année'].min())
        années_max = int(df_financial['Année'].max())
        années_range = st.slider(
            "Plage d'années à afficher",
            min_value=années_min, 
            max_value=années_max,
            value=(années_min, min(années_min + 10, années_max)),
            key=f"{key_prefix}year_range_{unique_id}"
        )
        
        # Filtrer les données selon la plage sélectionnée
        df_filtered = df_financial[(df_financial['Année'] >= années_range[0]) & (df_financial['Année'] <= années_range[1])]
        
        # Onglets regroupés
        tab1, tab2 = st.tabs(["Vue d'ensemble financière", "Analyse PPA détaillée"])
        
        with tab1:
            # Graphique combiné principal
            st.markdown("### Principaux flux financiers")
            
            fig = go.Figure()
            
            # Barres pour revenus et OPEX
            fig.add_trace(go.Bar(
                x=df_filtered['Année'],
                y=df_filtered['Revenus'],
                name='Revenus',
                marker_color='green'
            ))
            
            fig.add_trace(go.Bar(
                x=df_filtered['Année'],
                y=df_filtered['OPEX'],
                name='OPEX',
                marker_color='red'
            ))
            
            # Lignes pour EBITDA et Free Cash Flow
            fig.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['EBITDA'],
                name='EBITDA',
                mode='lines+markers',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['Free Cash Flow'],
                name='Free Cash Flow',
                mode='lines+markers',
                line=dict(color='purple', width=2),
                marker=dict(size=6)
            ))
            
            # Flux cumulé sur axe secondaire
            fig.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['Flux Cumulé'],
                name='Flux Cumulé',
                mode='lines+markers',
                line=dict(color='orange', width=2),
                marker=dict(size=6),
                yaxis="y2"
            ))
            
            # Ligne zéro
            fig.add_shape(
                type="line",
                x0=df_filtered['Année'].min(),
                y0=0,
                x1=df_filtered['Année'].max(),
                y1=0,
                line=dict(color="black", width=2, dash="dash")
            )
            
            fig.update_layout(
                title="Évolution des flux financiers",
                xaxis_title="Année",
                yaxis_title="Montant (€)",
                yaxis2=dict(
                    title="Flux Cumulé (€)",
                    overlaying="y",
                    side="right"
                ),
                barmode='group',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}combined_chart_{scenario_name}_{unique_id}")
            
            # DSCR dans un graphique séparé
            st.markdown("### DSCR (Ratio de couverture du service de la dette)")
            
            fig_dscr = go.Figure()
            fig_dscr.add_trace(go.Scatter(
                x=df_filtered['Année'],
                y=df_filtered['DSCR'],
                name='DSCR',
                mode='lines+markers',
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ))
            
            # Ligne DSCR cible
            target_dscr = st.session_state.config.get('target_dscr', 1.2)
            fig_dscr.add_shape(
                type="line",
                x0=df_filtered['Année'].min(),
                y0=target_dscr,
                x1=df_filtered['Année'].max(),
                y1=target_dscr,
                line=dict(color="red", width=2, dash="dash")
            )
            
            fig_dscr.add_annotation(
                x=df_filtered['Année'].max(),
                y=target_dscr,
                text=f"DSCR Cible = {target_dscr}",
                showarrow=False,
                yshift=10,
                font=dict(color="red")
            )
            
            fig_dscr.update_layout(
                xaxis_title="Année",
                yaxis_title="DSCR",
                height=400  # Hauteur réduite
            )
            
            st.plotly_chart(fig_dscr, use_container_width=True, key=f"{key_prefix}dscr_chart_{scenario_name}_{unique_id}")
            
            # Tableau détaillé accessible via un expandeur
            with st.expander("Tableau détaillé des flux financiers"):
                st.dataframe(df_financial, key=f"{key_prefix}financial_df_{scenario_name}_{unique_id}")
        
        with tab2:
            # Calculer et afficher l'analyse PPA
            ppa_results = self.create_ppa_cashflow_analysis(scenario_name)
            self.display_ppa_cashflow_analysis(ppa_results, scenario_name)
            
            # Comparaison PVSOL intégrée dans l'onglet
            st.markdown("### Comparaison PVSOL")
            st.info("Ce tableau compare le calcul du cashflow avec la méthode PVSOL, basé sur les paramètres spécifiques configurés.")
            
            df_pvs_financial = pd.DataFrame({
                "Année": results['years'],
                "Revenus Revente PVSOL": results['pvs_revenues_feedin'],
                "Revenus Economies PVSOL": results['pvs_revenues_avoided'],
                "OPEX PVSOL": results['pvs_opex'],
                "Cashflow Annuel PVSOL": results['pvs_cash_flow'],
                "Cashflow Cumulé PVSOL": results['pvs_cumulative_cash_flow']
            })
            
            # Investissement en année 0
            invest = np.zeros(len(results['years']))
            invest[0] = -results['capex']
            df_pvs_financial.insert(1, "Investissement", invest)
            
            st.dataframe(df_pvs_financial, key=f"{key_prefix}pvs_financial_df_{scenario_name}_{unique_id}")
    
    def display_scenarios_comparison(self, results):
        """
        Affiche la comparaison des scénarios
        
        Args:
            results: Dictionnaire contenant les résultats pour chaque scénario
        """
        st.markdown("### Comparaison des Scénarios")
        
        # Créer un DataFrame pour comparer les indicateurs clés
        comparison_data = []
        
        for scenario_name, scenario_results in results.items():
            comparison_data.append({
                "Scénario": scenario_name,
                "ROI (%)": scenario_results['roi'] * 100,
                "TRI (%)": scenario_results['irr'] * 100 if scenario_results['irr'] is not None else None,
                "VAN (€)": scenario_results['npv'],
                "Période de Récupération (ans)": scenario_results['payback_period'],
                "DSCR moyen": scenario_results['avg_dscr'],
                "Taux d'Autoconsommation (%)": scenario_results['autoconsumption_rate'] * 100,
                "Production Annuelle (kWh)": scenario_results['annual_production'][-1],
                "Surplus Annuel (kWh)": scenario_results['annual_surplus'][-1],
                # CORRECTION: Ajout du WACC
                "WACC (%)": scenario_results['wacc'] * 100
            })
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Afficher le tableau de comparaison
        st.dataframe(df_comparison.style.highlight_max(subset=['ROI (%)', 'TRI (%)', 'VAN (€)', 'DSCR moyen']).highlight_min(subset=['Période de Récupération (ans)', 'WACC (%)']), use_container_width=True)
        
        # Créer des graphiques de comparaison
        st.markdown("### Graphiques Comparatifs")
        
        # Comparaison des ROI, TRI, VAN
        fig1 = go.Figure()
        
        fig1.add_trace(go.Bar(
            x=[r["Scénario"] for r in comparison_data],
            y=[r["ROI (%)"] for r in comparison_data],
            name='ROI (%)',
            marker_color='blue'
        ))
        
        fig1.add_trace(go.Bar(
            x=[r["Scénario"] for r in comparison_data],
            y=[r["TRI (%)"] if r["TRI (%)"] is not None else 0 for r in comparison_data],
            name='TRI (%)',
            marker_color='green'
        ))
        
        fig1.update_layout(
            title="Comparaison des ROI et TRI par Scénario",
            xaxis_title="Scénario",
            yaxis_title="Pourcentage (%)",
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Créer une clé unique basée sur les noms des scénarios
        scenario_key = "_".join(sorted(results.keys()))
        
        # Afficher le graphique
        st.plotly_chart(fig1, use_container_width=True, key=f"scenarios_roi_tri_chart_{scenario_key}")
        
        # Comparaison des VAN
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=[r["Scénario"] for r in comparison_data],
            y=[r["VAN (€)"] for r in comparison_data],
            name='VAN (€)',
            marker_color='purple'
        ))
        
        fig2.update_layout(
            title="Comparaison des VAN par Scénario",
            xaxis_title="Scénario",
            yaxis_title="VAN (€)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Afficher le graphique
        st.plotly_chart(fig2, use_container_width=True, key=f"scenarios_van_chart_{scenario_key}")
        
        # Comparaison des flux cumulés
        fig3 = go.Figure()
        
        for scenario_name, scenario_results in results.items():
            fig3.add_trace(go.Scatter(
                x=scenario_results['years'],
                y=scenario_results['cumulative_cash_flow'],
                name=scenario_name,
                mode='lines+markers'
            ))
        
        # Ajouter une ligne horizontale à zéro
        fig3.add_shape(
            type="line",
            x0=min([min(r['years']) for r in results.values()]),
            y0=0,
            x1=max([max(r['years']) for r in results.values()]),
            y1=0,
            line=dict(
                color="black",
                width=2,
                dash="dash",
            )
        )
        
        fig3.update_layout(
            title="Comparaison des Flux Cumulés par Scénario",
            xaxis_title="Année",
            yaxis_title="Flux Cumulé (€)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Afficher le graphique
        st.plotly_chart(fig3, use_container_width=True, key=f"scenarios_cash_flow_chart_{scenario_key}")
    
    def display_sensitivity_analysis(self, results, parameter, unit):
        """
        Affiche les résultats de l'analyse de sensibilité
        
        Args:
            results: Dictionnaire contenant les résultats pour chaque valeur du paramètre
            parameter: Paramètre qui a été varié
            unit: Unité du paramètre
        """
        st.markdown("### Résultats de l'Analyse de Sensibilité")
        
        # Extraire les valeurs testées et les résultats correspondants
        values = list(results.keys())
        
        # Créer un DataFrame pour faciliter la création de graphiques
        df_sensitivity = pd.DataFrame({
            "Valeur": values,
            "ROI (%)": [results[v]['roi'] * 100 for v in values],
            "TRI (%)": [results[v]['irr'] * 100 if results[v]['irr'] is not None else 0 for v in values],
            "VAN (€)": [results[v]['npv'] for v in values],
            "Période de Récupération (ans)": [results[v]['payback_period'] if results[v]['payback_period'] != float('inf') else 30 for v in values],
            "DSCR moyen": [results[v]['avg_dscr'] if results[v]['avg_dscr'] != float('inf') else 5 for v in values],
            # CORRECTION: Ajout du WACC
            "WACC (%)": [results[v]['wacc'] * 100 for v in values]
        })
        
        # Afficher le tableau des résultats
        st.dataframe(df_sensitivity, use_container_width=True)
        
        # Créer des graphiques de sensibilité
        st.markdown("### Graphiques de Sensibilité")
        
        # Créer une clé unique pour les graphiques basée sur le paramètre et ses valeurs
        analysis_key = f"{parameter}_{min(values)}_{max(values)}"
        
        # Graphique ROI et TRI en fonction du paramètre
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=df_sensitivity["Valeur"],
            y=df_sensitivity["ROI (%)"],
            name='ROI (%)',
            mode='lines+markers',
            line=dict(color='blue', width=3),
            marker=dict(size=8)
        ))
        
        fig1.add_trace(go.Scatter(
            x=df_sensitivity["Valeur"],
            y=df_sensitivity["TRI (%)"],
            name='TRI (%)',
            mode='lines+markers',
            line=dict(color='green', width=3),
            marker=dict(size=8)
        ))
        
        fig1.update_layout(
            title=f"Sensibilité des ROI et TRI au {parameter} ({unit})",
            xaxis_title=f"{parameter} ({unit})",
            yaxis_title="Pourcentage (%)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Afficher le graphique
        st.plotly_chart(fig1, use_container_width=True, key=f"sensitivity_roi_tri_chart_{analysis_key}")
        
        # Graphique VAN en fonction du paramètre
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(
            x=df_sensitivity["Valeur"],
            y=df_sensitivity["VAN (€)"],
            name='VAN (€)',
            mode='lines+markers',
            line=dict(color='purple', width=3),
            marker=dict(size=8)
        ))
        
        # Ajouter une ligne horizontale à zéro
        fig2.add_shape(
            type="line",
            x0=min(df_sensitivity["Valeur"]),
            y0=0,
            x1=max(df_sensitivity["Valeur"]),
            y1=0,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            )
        )
        
        fig2.update_layout(
            title=f"Sensibilité de la VAN au {parameter} ({unit})",
            xaxis_title=f"{parameter} ({unit})",
            yaxis_title="VAN (€)"
        )
        
        # Afficher le graphique
        st.plotly_chart(fig2, use_container_width=True, key=f"sensitivity_van_chart_{analysis_key}")
        
        # Graphique Période de Récupération et DSCR en fonction du paramètre
        fig3 = go.Figure()
        
        fig3.add_trace(go.Scatter(
            x=df_sensitivity["Valeur"],
            y=df_sensitivity["Période de Récupération (ans)"],
            name='Période de Récupération (ans)',
            mode='lines+markers',
            line=dict(color='orange', width=3),
            marker=dict(size=8),
            yaxis="y"
        ))
        
        fig3.add_trace(go.Scatter(
            x=df_sensitivity["Valeur"],
            y=df_sensitivity["DSCR moyen"],
            name='DSCR moyen',
            mode='lines+markers',
            line=dict(color='red', width=3),
            marker=dict(size=8),
            yaxis="y2"
        ))
        
        # Ajouter une ligne horizontale pour le DSCR cible
        target_dscr = st.session_state.config['target_dscr']
        fig3.add_shape(
            type="line",
            x0=min(df_sensitivity["Valeur"]),
            y0=target_dscr,
            x1=max(df_sensitivity["Valeur"]),
            y1=target_dscr,
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            yref="y2"
        )
        
        fig3.update_layout(
            title=f"Sensibilité de la Période de Récupération et du DSCR au {parameter} ({unit})",
            xaxis_title=f"{parameter} ({unit})",
            yaxis=dict(
                title="Période de Récupération (ans)",
                side="left"
            ),
            yaxis2=dict(
                title="DSCR moyen",
                side="right",
                overlaying="y"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Afficher le graphique
        st.plotly_chart(fig3, use_container_width=True, key=f"sensitivity_dscr_chart_{analysis_key}")
        
        # CORRECTION: Graphique du WACC en fonction du paramètre
        if parameter in ["debt_ratio", "debt_term_years"]:
            fig4 = go.Figure()
            
            fig4.add_trace(go.Scatter(
                x=df_sensitivity["Valeur"],
                y=df_sensitivity["WACC (%)"],
                name='WACC (%)',
                mode='lines+markers',
                line=dict(color='brown', width=3),
                marker=dict(size=8)
            ))
            
            fig4.update_layout(
                title=f"Sensibilité du WACC au {parameter} ({unit})",
                xaxis_title=f"{parameter} ({unit})",
                yaxis_title="WACC (%)"
            )
            
            # Afficher le graphique
            st.plotly_chart(fig4, use_container_width=True, key=f"sensitivity_wacc_chart_{analysis_key}")
    
    def assess_profitability(self, results):
        """
        Évalue la rentabilité du projet en fonction des résultats
        
        Args:
            results: Dictionnaire contenant les résultats financiers
        """
        # Critères de rentabilité
        roi_min = 0.05  # 5%
        irr_min = 0.04  # 4%
        payback_max = 15  # 15 ans
        dscr_min = results.get('dscr_min', dscr.min() if len(dscr) > 0 else 0)
        
        # Obtenir le DSCR cible (avec une valeur par défaut de 1.2)
        target_dscr = st.session_state.config.get('target_dscr', 1.2)
        
        # Colorer le DSCR min en fonction de sa valeur
        if dscr_min >= target_dscr:
            dscr_min_color = "green"
        elif dscr_min >= 1.0:
            dscr_min_color = "orange"
        else:
            dscr_min_color = "red"
        
        # Vérifier les critères
        roi_ok = results['roi'] >= roi_min
        irr_ok = results['irr'] is not None and results['irr'] >= irr_min
        payback_ok = results['payback_period'] != float('inf') and results['payback_period'] <= payback_max
        dscr_ok = results['avg_dscr'] >= dscr_min
        
        # Tarif EDF
        tarif_edf = st.session_state.config['tarif_edf_reference']
        competitive = results['prix_revente'] < tarif_edf
        
        # Afficher un message sur la rentabilité
        st.markdown("### Évaluation de la Rentabilité")
        
        # Nombre de critères respectés
        n_criteria_met = sum([roi_ok, irr_ok, payback_ok, dscr_ok])
        
        if n_criteria_met == 4 and competitive:
            st.success(f"✅ Le projet est rentable et compétitif avec un prix de revente de {results['prix_revente']:.2f} €/kWh (vs {tarif_edf:.2f} €/kWh pour EDF).")
        elif n_criteria_met >= 3 and competitive:
            st.info(f"ℹ️ Le projet est globalement rentable et compétitif avec un prix de revente de {results['prix_revente']:.2f} €/kWh (vs {tarif_edf:.2f} €/kWh pour EDF), mais certains indicateurs sont limites.")
        elif competitive:
            st.warning(f"⚠️ Le projet est compétitif avec un prix de revente de {results['prix_revente']:.2f} €/kWh (vs {tarif_edf:.2f} €/kWh pour EDF), mais sa rentabilité est insuffisante.")
        elif n_criteria_met >= 3:
            st.warning(f"⚠️ Le projet est rentable, mais non compétitif avec un prix de revente de {results['prix_revente']:.2f} €/kWh (vs {tarif_edf:.2f} €/kWh pour EDF).")
        else:
            st.error(f"❌ Le projet n'est ni rentable ni compétitif avec un prix de revente de {results['prix_revente']:.2f} €/kWh (vs {tarif_edf:.2f} €/kWh pour EDF).")
        
        # Détailler les critères
        with st.expander("Détails des critères de rentabilité"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"- ROI > {roi_min*100}% : {'✅' if roi_ok else '❌'} ({results['roi']*100:.2f}%)")
                st.markdown(f"- TRI > {irr_min*100}% : {'✅' if irr_ok else '❌'} ({results['irr']*100:.2f}% {'ou Non calculable' if results['irr'] is None else ''})")
            
            with col2:
                st.markdown(f"- Période de Récupération < {payback_max} ans : {'✅' if payback_ok else '❌'} ({results['payback_period']:.2f} ans {'ou Jamais' if results['payback_period'] == float('inf') else ''})")
                st.markdown(f"- DSCR moyen > {dscr_min} : {'✅' if dscr_ok else '❌'} ({results['avg_dscr']:.2f})")
            
            st.markdown(f"- Prix de revente < Tarif EDF ({tarif_edf:.2f} €/kWh) : {'✅' if competitive else '❌'} ({results['prix_revente']:.2f} €/kWh)")
    
    def create_ppa_cashflow_analysis(self, scenario_name=None):
        """
        Crée une analyse des flux de trésorerie PPA sur 30 ans
        
        Args:
            scenario_name: Nom du scénario à utiliser (si None, utilise le premier disponible)
            
        Returns:
            tuple: (DataFrame contenant l'analyse complète des flux PPA, métadonnées)
        """
        if not hasattr(st.session_state, 'economic_results') or not st.session_state.economic_results:
            st.error("Aucun résultat économique disponible. Veuillez d'abord effectuer une analyse économique.")
            return None
        
        # Si aucun scénario n'est spécifié, utiliser le premier disponible
        if scenario_name is None:
            scenario_name = list(st.session_state.economic_results.keys())[0]
            st.info(f"Aucun scénario spécifié. Utilisation du scénario par défaut : {scenario_name}")
        
        # Vérifier que le scénario existe
        if scenario_name not in st.session_state.economic_results:
            st.error(f"Le scénario {scenario_name} n'existe pas.")
            return None
        
        # Récupérer les résultats
        results = st.session_state.economic_results[scenario_name]
        
        # Validation des paramètres de configuration requis
        required_params = ['capex', 'prix_vente_initial', 'taux_inflation', 'degradation_rate']
        missing_params = [param for param in required_params if param not in st.session_state.config]
        if missing_params:
            st.error(f"Paramètres manquants dans la configuration : {', '.join(missing_params)}")
            return None
        
        # Récupérer les paramètres de configuration
        config = st.session_state.config
        
        # Nombre d'années pour l'analyse (30 ans)
        n_years = 30
        
        # Préparer les données pour l'analyse PPA
        years = np.arange(0, n_years + 1)  # 0 à 30 (inclus)
        
        # Initialiser les tableaux
        capex = np.zeros(n_years + 1)
        subventions = np.zeros(n_years + 1)
        production = np.zeros(n_years + 1)
        revenus_client = np.zeros(n_years + 1)
        revenus_fournisseur = np.zeros(n_years + 1)
        revenus_totaux = np.zeros(n_years + 1)
        opex = np.zeros(n_years + 1)
        remplacement_onduleur = np.zeros(n_years + 1)
        demantelement = np.zeros(n_years + 1)
        ebitda = np.zeros(n_years + 1)
        ebt = np.zeros(n_years + 1)
        ebt_cumule = np.zeros(n_years + 1)
        financement = np.zeros(n_years + 1)
        interets = np.zeros(n_years + 1)
        
        # Remplir le CAPEX en année 0
        capex[0] = config['capex']
        
        # Subventions (si disponible dans la configuration, sinon 0)
        subventions[0] = config.get('subventions', 0)
        if subventions[0] > 0:
            st.info(f"Subvention appliquée : {subventions[0]:,.2f} €")
        
        # Vérifier si les données de production sont suffisantes
        if len(results['annual_production']) < n_years:
            st.warning(f"Les données de production ne couvrent que {len(results['annual_production'])} années. Une extrapolation sera effectuée pour les {n_years - len(results['annual_production'])} années restantes.")
        
        # Remplir les valeurs pour chaque année
        for i in range(1, n_years + 1):
            # Production avec dégradation des modules
            if i <= len(results['annual_production']):
                production[i] = results['annual_production'][i-1]
            else:
                # Extrapolation si les résultats n'ont pas 30 ans
                last_year_index = min(i-1, len(results['annual_production'])-1)
                degradation_factor = (1 - config['degradation_rate']) ** (i - last_year_index - 1)
                production[i] = results['annual_production'][last_year_index] * degradation_factor
            
            # Revenus
            if i <= len(results['annual_autoconsumption']):
                # Prix de revente au client (autoconsommation)
                prix_client = config['prix_vente_initial'] * (1 + config['taux_inflation']/100) ** (i-1)
                revenus_client[i] = results['annual_autoconsumption'][i-1] * prix_client
                
                # Revenus de revente du surplus au fournisseur
                prix_fournisseur = config.get('tarif_surplus', config['prix_vente_initial'] * 0.6)
                prix_fournisseur_indexe = prix_fournisseur * (1 + config['taux_inflation']/100) ** (i-1)
                revenus_fournisseur[i] = results['annual_surplus'][i-1] * prix_fournisseur_indexe
            else:
                # Extrapolation
                last_year_index = min(i-1, len(results['annual_autoconsumption'])-1)
                degradation_factor = (1 - config['degradation_rate']) ** (i - last_year_index - 1)
                
                # Extrapolation des revenus client
                prix_client = config['prix_vente_initial'] * (1 + config['taux_inflation']/100) ** (i-1)
                revenus_client[i] = results['annual_autoconsumption'][last_year_index] * degradation_factor * prix_client
                
                # Extrapolation des revenus fournisseur
                prix_fournisseur = config.get('tarif_surplus', config['prix_vente_initial'] * 0.6)
                prix_fournisseur_indexe = prix_fournisseur * (1 + config['taux_inflation']/100) ** (i-1)
                revenus_fournisseur[i] = results['annual_surplus'][last_year_index] * degradation_factor * prix_fournisseur_indexe
            
            # Revenus totaux
            revenus_totaux[i] = revenus_client[i] + revenus_fournisseur[i]
            
            # OPEX (charges d'exploitation)
            if i <= len(results['opex']):
                opex[i] = results['opex'][i-1]
            else:
                # Extrapolation de l'OPEX avec inflation
                last_year_index = min(i-1, len(results['opex'])-1)
                inflation_factor = (1 + config['taux_inflation']/100) ** (i - last_year_index - 1)
                opex[i] = results['opex'][last_year_index] * inflation_factor
            
            # Remplacement de l'onduleur
            duree_onduleur = config.get('duree_onduleur', 15)
            cout_onduleur = config.get('cout_onduleur', config['capex'] * 0.1)
            
            if i % duree_onduleur == 0 and i != 0 and i != n_years:
                remplacement_onduleur[i] = cout_onduleur * (1 + config['taux_inflation']/100) ** (i-1)
                if i == duree_onduleur:
                    st.info(f"Premier remplacement d'onduleur prévu en année {i} pour un coût de {remplacement_onduleur[i]:,.2f} €")
            
            # Démantèlement à l'année 30
            if i == n_years:
                demantelement[i] = config.get('cout_demantelement', config['capex'] * 0.05)
                st.info(f"Coût de démantèlement prévu en année {i} : {demantelement[i]:,.2f} €")
            
            # EBITDA
            ebitda[i] = revenus_totaux[i] - opex[i]
            
            # EBT (Earnings Before Tax) - revenus moins tous les coûts
            ebt[i] = ebitda[i] - remplacement_onduleur[i] - demantelement[i] - interets[i]
        
        # Calculs financiers
        # EBT cumulé
        ebt_cumule[0] = -capex[0] + subventions[0]
        for i in range(1, n_years + 1):
            ebt_cumule[i] = ebt_cumule[i-1] + ebt[i]
        
        # Financement et intérêts
        if 'debt_service' in results and 'interest_paid' in results:
            for i in range(1, n_years + 1):
                if i <= len(results['debt_service']):
                    financement[i] = results['debt_service'][i-1]
                    interets[i] = results['interest_paid'][i-1]
        else:
            st.warning("Données de financement non disponibles dans les résultats. Utilisation d'un calcul simplifié.")
            # Calcul simplifié
            debt_ratio = config.get('debt_ratio', 0.8)
            loan_amount = capex[0] * debt_ratio
            loan_term = config.get('debt_term_years', 15)
            interest_rate = config.get('debt_rate', 2.0) / 100
            
            # Calcul de l'annuité
            if interest_rate > 0:
                annuity = loan_amount * interest_rate * (1 + interest_rate) ** loan_term / ((1 + interest_rate) ** loan_term - 1)
            else:
                annuity = loan_amount / loan_term
            
            remaining_debt = loan_amount
            for i in range(1, n_years + 1):
                if i <= loan_term:
                    interets[i] = remaining_debt * interest_rate
                    principal = min(annuity - interets[i], remaining_debt)
                    financement[i] = interets[i] + principal
                    remaining_debt -= principal
        
        # Calcul VAN et TRI
        cashflows = [-capex[0] + subventions[0]]  # Année 0
        for i in range(1, n_years + 1):
            cashflow_i = ebitda[i] - remplacement_onduleur[i] - demantelement[i] - financement[i]
            cashflows.append(cashflow_i)
        
        discount_rate = config.get('cout_fonds_propres', 8.0) / 100
        
        # VAN (NPV)
        try:
            npv = npf.npv(discount_rate, cashflows)
        except Exception as e:
            st.error(f"Erreur lors du calcul de la VAN : {str(e)}")
            npv = 0
        
        # TRI (IRR)
        try:
            irr = npf.irr(cashflows)
        except Exception as e:
            st.warning(f"Impossible de calculer le TRI : {str(e)}")
            irr = None
        
        # Créer le DataFrame pour l'analyse PPA
        data = {
            'Année': years,
            'Investissement initial (CAPEX)': capex,
            'Subvention': subventions,
            'Production (kWh)': production,
            'Revenus vente client': revenus_client,
            'Revenus revente surplus': revenus_fournisseur,
            'Revenus totaux': revenus_totaux,
            'Charges exploitation (OPEX)': opex,
            'Remplacement onduleur': remplacement_onduleur,
            'Démantèlement': demantelement,
            'EBITDA': ebitda,
            'Intérêts': interets,
            'Financement': financement,
            'EBT': ebt,
            'EBT cumulé': ebt_cumule,
        }
        
        df_ppa = pd.DataFrame(data)
        
        # Ajouter des métadonnées
        metadata = {
            'VAN': npv,
            'TRI': irr * 100 if irr is not None else None,
            'Scénario': scenario_name,
            'Durée analyse': n_years,
            'Taux actualisation': discount_rate * 100,
            'Production totale': production.sum(),
            'Revenus totaux': revenus_totaux.sum(),
            'OPEX total': opex.sum(),
            'Date analyse': datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        
        return df_ppa, metadata
    
    def display_ppa_cashflow_analysis(self, results, scenario_name):
        """
        Affiche l'analyse des flux de trésorerie PPA
        
        Args:
            results: Tuple contenant (DataFrame d'analyse PPA, métadonnées)
            scenario_name: Nom du scénario utilisé
        """
        if results is None or len(results) != 2:
            st.error("Impossible d'afficher l'analyse des flux de trésorerie PPA")
            return
        
        df_ppa, metadata = results
        
        # Créer un ID unique basé sur le nom du scénario et un timestamp
        unique_id = f"{scenario_name}_{int(time.time()*1000) % 10000}"
        
        st.markdown("### Analyse des flux de trésorerie – PPA")
        st.markdown(f"#### Cashflow – Analyse PPA : Projet photovoltaïque [{scenario_name}]")
        
        # Afficher les métadonnées principales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("VAN", f"{metadata['VAN']:,.2f} €")
        with col2:
            st.metric("TRI", f"{metadata['TRI']:.2f}%" if metadata['TRI'] is not None else "N/A")
        with col3:
            st.metric("Durée d'analyse", f"{metadata['Durée analyse']} ans")
        
        # Afficher le tableau des flux
        st.dataframe(df_ppa.style.format({
            'Investissement initial (CAPEX)': '{:,.2f} €',
            'Subvention': '{:,.2f} €',
            'Production (kWh)': '{:,.2f}',
            'Revenus vente client': '{:,.2f} €',
            'Revenus revente surplus': '{:,.2f} €',
            'Revenus totaux': '{:,.2f} €',
            'Charges exploitation (OPEX)': '{:,.2f} €',
            'Remplacement onduleur': '{:,.2f} €',
            'Démantèlement': '{:,.2f} €',
            'EBITDA': '{:,.2f} €',
            'Intérêts': '{:,.2f} €',
            'Financement': '{:,.2f} €',
            'EBT': '{:,.2f} €',
            'EBT cumulé': '{:,.2f} €'
        }), use_container_width=True)
        
        # Créer un graphique pour visualiser l'évolution des flux
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_ppa['Année'],
            y=df_ppa['Revenus totaux'],
            name='Revenus totaux',
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            x=df_ppa['Année'],
            y=df_ppa['Charges exploitation (OPEX)'],
            name='OPEX',
            marker_color='red'
        ))
        
        fig.add_trace(go.Scatter(
            x=df_ppa['Année'],
            y=df_ppa['EBITDA'],
            name='EBITDA',
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_ppa['Année'],
            y=df_ppa['EBT cumulé'],
            name='EBT cumulé',
            mode='lines+markers',
            line=dict(color='purple', width=2),
            marker=dict(size=6)
        ))
        
        # Ajouter une ligne horizontale à zéro
        fig.add_shape(
            type="line",
            x0=df_ppa['Année'].min(),
            y0=0,
            x1=df_ppa['Année'].max(),
            y1=0,
            line=dict(
                color="black",
                width=2,
                dash="dash",
            )
        )
        
        fig.update_layout(
            title="Évolution des flux financiers PPA",
            xaxis_title="Année",
            yaxis_title="Montant (€)",
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Utiliser une clé unique pour le graphique
        st.plotly_chart(fig, use_container_width=True, key=f"ppa_chart_{unique_id}")
        
        # Afficher les tableaux détaillés
        with st.expander("Afficher les détails année par année"):
            # Sélection des années à afficher
            selected_year = st.slider("Sélectionner une année spécifique", 0, metadata['Durée analyse'], 0, key=f"year_slider_{unique_id}")
            
            # Afficher les détails pour l'année sélectionnée
            year_data = df_ppa[df_ppa['Année'] == selected_year].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Investissements et Production")
                st.markdown(f"**CAPEX:** {year_data['Investissement initial (CAPEX)']:,.2f} €")
                st.markdown(f"**Subvention:** {year_data['Subvention']:,.2f} €")
                st.markdown(f"**Production:** {year_data['Production (kWh)']:,.2f} kWh")
                
                if year_data['Remplacement onduleur'] > 0:
                    st.markdown(f"**Remplacement onduleur:** {year_data['Remplacement onduleur']:,.2f} €")
                
                if year_data['Démantèlement'] > 0:
                    st.markdown(f"**Coût démantèlement:** {year_data['Démantèlement']:,.2f} €")
            
            with col2:
                st.markdown("#### Revenus")
                st.markdown(f"**Revenus client:** {year_data['Revenus vente client']:,.2f} €")
                st.markdown(f"**Revenus surplus:** {year_data['Revenus revente surplus']:,.2f} €")
                st.markdown(f"**Revenus totaux:** {year_data['Revenus totaux']:,.2f} €")
            
            with col3:
                st.markdown("#### Charges et Résultats")
                st.markdown(f"**OPEX:** {year_data['Charges exploitation (OPEX)']:,.2f} €")
                st.markdown(f"**EBITDA:** {year_data['EBITDA']:,.2f} €")
                st.markdown(f"**Intérêts:** {year_data['Intérêts']:,.2f} €")
                st.markdown(f"**EBT:** {year_data['EBT']:,.2f} €")
                st.markdown(f"**EBT cumulé:** {year_data['EBT cumulé']:,.2f} €")
        
        # Option pour exporter le tableau PPA au format Excel avec mise en forme professionnelle
        with st.expander("Exporter l'analyse financière PPA"):
            if st.button("Créer un fichier Excel professionnel", key=f"excel_button_{unique_id}"):
                # Créer un buffer pour stocker le fichier Excel
                buffer = io.BytesIO()
                
                # Créer un writer Excel avec xlsxwriter pour permettre la mise en forme
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    # Écrire les données dans la feuille Excel
                    df_ppa.to_excel(writer, sheet_name='Analyse PPA', index=False)
                    
                    # Récupérer le classeur et la feuille de calcul
                    workbook = writer.book
                    worksheet = writer.sheets['Analyse PPA']
                    
                    # Définir les formats pour les cellules
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    currency_format = workbook.add_format({
                        'num_format': '# ##0,00 €',
                        'border': 1
                    })
                    
                    number_format = workbook.add_format({
                        'num_format': '# ##0,00',
                        'border': 1
                    })
                    
                    integer_format = workbook.add_format({
                        'num_format': '0',
                        'border': 1
                    })
                    
                    percent_format = workbook.add_format({
                        'num_format': '0.00%',
                        'border': 1
                    })
                    
                    title_format = workbook.add_format({
                        'bold': True,
                        'font_size': 16,
                        'align': 'center',
                        'valign': 'vcenter',
                        'border': 0
                    })
                    
                    subtitle_format = workbook.add_format({
                        'bold': True,
                        'font_size': 12,
                        'align': 'center',
                        'valign': 'vcenter',
                        'border': 0
                    })
                    
                    # Appliquer le format aux en-têtes
                    for col_num, value in enumerate(df_ppa.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Appliquer les formats aux colonnes
                    worksheet.set_column('A:A', 8, integer_format)  # Année
                    worksheet.set_column('B:B', 15, currency_format)  # CAPEX
                    worksheet.set_column('C:C', 15, currency_format)  # Subvention
                    worksheet.set_column('D:D', 15, number_format)    # Production
                    worksheet.set_column('E:E', 15, currency_format)  # Revenus client
                    worksheet.set_column('F:F', 15, currency_format)  # Revenus surplus
                    worksheet.set_column('G:G', 15, currency_format)  # Revenus totaux
                    worksheet.set_column('H:H', 15, currency_format)  # OPEX
                    worksheet.set_column('I:I', 15, currency_format)  # Remplacement onduleur
                    worksheet.set_column('J:J', 15, currency_format)  # Démantèlement
                    worksheet.set_column('K:K', 15, currency_format)  # EBITDA
                    worksheet.set_column('L:L', 15, currency_format)  # Intérêts
                    worksheet.set_column('M:M', 15, currency_format)  # Financement
                    worksheet.set_column('N:N', 15, currency_format)  # EBT
                    worksheet.set_column('O:O', 15, currency_format)  # EBT cumulé
                    
                    # Fusionner des cellules pour le titre et sous-titre
                    worksheet.merge_range('A1:O1', "", title_format)
                    worksheet.merge_range('A2:O2', "", subtitle_format)
                    worksheet.merge_range('A3:O3', "", subtitle_format)
                    
                    # Décaler les données vers le bas pour insérer le titre et les métadonnées
                    worksheet.write('A1', f"Analyse des flux de trésorerie – PPA", title_format)
                    worksheet.write('A2', f"Projet photovoltaïque – {scenario_name}", subtitle_format)
                    worksheet.write('A3', f"VAN: {metadata['VAN']:,.2f} € | TRI: {metadata['TRI']:.2f}% | Durée: {metadata['Durée analyse']} ans", subtitle_format)
                    
                    # Ajouter une feuille de résumé avec les chiffres clés
                    df_summary = pd.DataFrame({
                        'Indicateur': ['VAN', 'TRI', 'Durée d\'analyse', 'CAPEX', 'OPEX année 1', 'Revenus année 1', 'Payback period'],
                        'Valeur': [
                            f"{metadata['VAN']:,.2f} €",
                            f"{metadata['TRI']:.2f}%" if metadata['TRI'] is not None else "N/A",
                            f"{metadata['Durée analyse']} ans",
                            f"{df_ppa['Investissement initial (CAPEX)'].iloc[0]:,.2f} €",
                            f"{df_ppa['Charges exploitation (OPEX)'].iloc[1]:,.2f} €",
                            f"{df_ppa['Revenus totaux'].iloc[1]:,.2f} €",
                            "Calcul en cours..."  # Placeholder pour le calcul du payback
                        ]
                    })
                    
                    # Calculer le payback period
                    payback_year = None
                    for i, row in df_ppa.iterrows():
                        if row['EBT cumulé'] >= 0 and i > 0:  # i > 0 pour ignorer l'année 0
                            # Interpolation pour une estimation plus précise
                            if i > 1 and df_ppa.iloc[i-1]['EBT cumulé'] < 0:
                                last_neg = df_ppa.iloc[i-1]['EBT cumulé']
                                current = row['EBT cumulé']
                                fraction = abs(last_neg) / (current - last_neg)
                                payback_year = row['Année'] - 1 + fraction
                            else:
                                payback_year = row['Année']
                            break
                    
                    # Mettre à jour la valeur du payback period
                    if payback_year is not None:
                        df_summary.loc[df_summary['Indicateur'] == 'Payback period', 'Valeur'] = f"{payback_year:.2f} ans"
                    else:
                        df_summary.loc[df_summary['Indicateur'] == 'Payback period', 'Valeur'] = "Supérieur à 30 ans"
                    
                    # Ajouter la feuille de résumé
                    df_summary.to_excel(writer, sheet_name='Résumé', index=False)
                    summary_sheet = writer.sheets['Résumé']
                    
                    # Formater la feuille de résumé
                    summary_sheet.set_column('A:A', 20)
                    summary_sheet.set_column('B:B', 25)
                    
                    # Ajouter un titre à la feuille de résumé
                    summary_sheet.merge_range('A1:B1', "", title_format)
                    summary_sheet.write('A1', f"Résumé Analyse PPA - {scenario_name}", title_format)
                    
                    # Décaler les données
                    for i, (idx, row) in enumerate(df_summary.iterrows(), start=3):
                        summary_sheet.write(i, 0, row['Indicateur'], header_format)
                        summary_sheet.write(i, 1, row['Valeur'])
                    
                    # Ajouter un graphique dans la feuille Excel
                    chart = workbook.add_chart({'type': 'column'})
                    
                    # Configurer le graphique
                    chart.add_series({
                        'name': 'Revenus totaux',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 6, 4+len(df_ppa)-1, 6],  # Revenus totaux
                        'fill': {'color': 'green'}
                    })
                    
                    chart.add_series({
                        'name': 'OPEX',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 7, 4+len(df_ppa)-1, 7],  # OPEX
                        'fill': {'color': 'red'}
                    })
                    
                    chart.add_series({
                        'name': 'EBITDA',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 10, 4+len(df_ppa)-1, 10],  # EBITDA
                        'type': 'line',
                        'line': {'color': 'blue', 'width': 2.5}
                    })
                    
                    # Configurer les axes et titres
                    chart.set_title({'name': 'Évolution des flux financiers'})
                    chart.set_x_axis({'name': 'Année'})
                    chart.set_y_axis({'name': 'Montant (€)'})
                    
                    # Insérer le graphique
                    chart_sheet = workbook.add_chartsheet('Graphique')
                    chart_sheet.set_chart(chart)
                    
                    # Ajouter un autre graphique pour l'EBT cumulé
                    ebt_chart = workbook.add_chart({'type': 'line'})
                    
                    ebt_chart.add_series({
                        'name': 'EBT cumulé',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 14, 4+len(df_ppa)-1, 14],  # EBT cumulé
                        'line': {'color': 'purple', 'width': 2.5},
                        'marker': {'type': 'circle', 'size': 3}
                    })
                    
                    # Ajouter une ligne à zéro
                    ebt_chart.set_y_axis({
                        'name': 'Montant (€)',
                        'major_gridlines': {'visible': True},
                        'line': {'color': 'black'}
                    })
                    
                    ebt_chart.set_title({'name': 'Évolution de l\'EBT cumulé'})
                    ebt_chart.set_x_axis({'name': 'Année'})
                    
                    # Insérer le deuxième graphique
                    worksheet.insert_chart('Q5', ebt_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                
                # Proposer le téléchargement du fichier Excel
                buffer.seek(0)
                
                # Créer un nom de fichier avec le nom du scénario et la date
                today = datetime.now().strftime("%Y-%m-%d")
                filename = f"PPA_Cashflow_{scenario_name}_{today}.xlsx"
                
                st.download_button(
                    label="Télécharger le fichier Excel",
                    data=buffer,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_button_{unique_id}"
                )
    
    def generate_excel_report(self, df_ppa, metadata):
        """
        Génère un rapport Excel complet de l'analyse PPA
        
        Args:
            df_ppa: DataFrame contenant les données de l'analyse PPA
            metadata: Dictionnaire contenant les métadonnées de l'analyse
            
        Returns:
            bytes: Fichier Excel en format binaire
        """
        try:
            # Créer un buffer pour stocker le fichier Excel
            output = BytesIO()
            
            # Créer un writer Excel
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Écrire les données principales
                df_ppa.to_excel(writer, sheet_name='Analyse PPA', index=False)
                
                # Récupérer le workbook et le worksheet
                workbook = writer.book
                worksheet = writer.sheets['Analyse PPA']
                
                # Définir les formats
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D9D9D9',
                    'border': 1
                })
                
                money_format = workbook.add_format({
                    'num_format': '#,##0.00 €',
                    'border': 1
                })
                
                number_format = workbook.add_format({
                    'num_format': '#,##0.00',
                    'border': 1
                })
                
                percent_format = workbook.add_format({
                    'num_format': '0.00%',
                    'border': 1
                })
                
                # Appliquer les formats aux colonnes
                for idx, col in enumerate(df_ppa.columns):
                    # Définir la largeur de colonne
                    worksheet.set_column(idx, idx, 15)
                    
                    # Appliquer le format d'en-tête
                    worksheet.write(0, idx, col, header_format)
                    
                    # Appliquer les formats aux données
                    if 'Année' in col:
                        worksheet.set_column(idx, idx, 8, number_format)
                    elif any(x in col for x in ['Production', 'kWh']):
                        worksheet.set_column(idx, idx, 12, number_format)
                    elif any(x in col for x in ['€', 'CAPEX', 'Revenus', 'OPEX', 'EBITDA', 'EBT']):
                        worksheet.set_column(idx, idx, 15, money_format)
                    else:
                        worksheet.set_column(idx, idx, 12, number_format)
                
                # Créer une feuille pour les métadonnées
                metadata_df = pd.DataFrame([
                    ['Date de l\'analyse', metadata['Date analyse']],
                    ['Scénario', metadata['Scénario']],
                    ['Durée d\'analyse (ans)', metadata['Durée analyse']],
                    ['VAN', metadata['VAN']],
                    ['TRI', metadata['TRI'] if metadata['TRI'] is not None else 'N/A'],
                    ['Taux d\'actualisation', metadata['Taux actualisation'] / 100],
                    ['Production totale (kWh)', metadata['Production totale']],
                    ['Revenus totaux (€)', metadata['Revenus totaux']],
                    ['OPEX total (€)', metadata['OPEX total']]
                ], columns=['Paramètre', 'Valeur'])
                
                metadata_df.to_excel(writer, sheet_name='Métadonnées', index=False)
                
                # Formater la feuille des métadonnées
                worksheet_meta = writer.sheets['Métadonnées']
                worksheet_meta.set_column('A:A', 25)
                worksheet_meta.set_column('B:B', 20)
                
                # Appliquer les formats aux métadonnées
                for idx, (param, value) in enumerate(metadata_df.values, start=1):
                    if 'VAN' in param or 'Revenus' in param or 'OPEX' in param:
                        worksheet_meta.write(idx, 1, value, money_format)
                    elif 'TRI' in param or 'actualisation' in param:
                        if isinstance(value, (int, float)):
                            worksheet_meta.write(idx, 1, value, percent_format)
                        else:
                            worksheet_meta.write(idx, 1, value)
                    elif 'Production' in param:
                        worksheet_meta.write(idx, 1, value, number_format)
                    else:
                        worksheet_meta.write(idx, 1, value)
                
                # Ajouter un graphique
                chart = workbook.add_chart({'type': 'column'})
                
                # Configurer les séries pour le graphique
                chart.add_series({
                    'name': 'Revenus totaux',
                    'categories': ['Analyse PPA', 1, 0, len(df_ppa), 0],
                    'values': ['Analyse PPA', 1, df_ppa.columns.get_loc('Revenus totaux'), len(df_ppa), df_ppa.columns.get_loc('Revenus totaux')],
                    'fill': {'color': '#2E7D32'}
                })
                
                chart.add_series({
                    'name': 'OPEX',
                    'categories': ['Analyse PPA', 1, 0, len(df_ppa), 0],
                    'values': ['Analyse PPA', 1, df_ppa.columns.get_loc('Charges exploitation (OPEX)'), len(df_ppa), df_ppa.columns.get_loc('Charges exploitation (OPEX)')],
                    'fill': {'color': '#C62828'}
                })
                
                # Configurer le graphique
                chart.set_title({'name': 'Évolution des flux financiers PPA'})
                chart.set_x_axis({'name': 'Année'})
                chart.set_y_axis({'name': 'Montant (€)'})
                chart.set_size({'width': 720, 'height': 400})
                
                # Insérer le graphique dans une nouvelle feuille
                worksheet_chart = workbook.add_worksheet('Graphique')
                worksheet_chart.insert_chart('B2', chart)
            
            # Récupérer les données du buffer
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Erreur lors de la génération du rapport Excel : {str(e)}")
            return None
    
    def generate_excel_report_with_formulas(self, scenario_results, scenario_name):
        """
        Génère un rapport Excel avec des formules visibles pour TRI, VAN et Payback.
        
        Args:
            scenario_results: Le dictionnaire des résultats financiers du scénario
            scenario_name: Le nom du scénario
            
        Returns:
            bytes: Le fichier Excel en format bytes
        """
        if not scenario_results:
            return None
            
        # Créer un fichier Excel en mémoire
        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer)
        
        # Formats pour le workbook
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 
            'valign': 'vcenter', 'bg_color': '#D9E1F2', 'border': 1
        })
        header_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'center',
            'valign': 'vcenter', 'bg_color': '#E2EFDA', 'border': 1
        })
        money_format = workbook.add_format({
            'num_format': '#,##0.00 €', 'align': 'right', 'border': 1
        })
        percent_format = workbook.add_format({
            'num_format': '0.00%', 'align': 'right', 'border': 1
        })
        number_format = workbook.add_format({
            'num_format': '#,##0.00', 'align': 'right', 'border': 1
        })
        text_format = workbook.add_format({
            'align': 'left', 'border': 1
        })
        formula_format = workbook.add_format({
            'align': 'right', 'border': 1, 'italic': True, 'bg_color': '#FFEB9C'
        })
        
        # Feuille 1: Résumé
        summary_sheet = workbook.add_worksheet('Résumé')
        summary_sheet.set_column('A:A', 40)
        summary_sheet.set_column('B:B', 25)
        
        # Titre
        summary_sheet.merge_range('A1:B1', f'Analyse Financière - Scénario {scenario_name}', title_format)
        
        # Paramètres du projet
        row = 2
        summary_sheet.write(row, 0, 'Paramètres du Projet', header_format)
        summary_sheet.write(row, 1, '', header_format)
        row += 1
        
        # Écrire les paramètres de base
        params = [
            ('Puissance installée (kWc)', scenario_results.get('installed_capacity', 'N/A')),
            ('Investissement initial (€)', scenario_results.get('initial_investment', 'N/A')),
            ('Prix de revente (€/kWh)', scenario_results.get('ppa_price', 'N/A')),
            ('Durée du projet (années)', scenario_results.get('project_lifetime', 'N/A')),
            ('Taux WACC (%)', scenario_results.get('wacc', 'N/A') * 100 if scenario_results.get('wacc') is not None else 'N/A')
        ]
        
        for param, value in params:
            summary_sheet.write(row, 0, param, text_format)
            if isinstance(value, (int, float)):
                if 'Prix' in param or 'Investissement' in param:
                    summary_sheet.write(row, 1, value, money_format)
                elif 'Taux' in param:
                    summary_sheet.write(row, 1, value/100, percent_format)
                else:
                    summary_sheet.write(row, 1, value, number_format)
            else:
                summary_sheet.write(row, 1, value, text_format)
            row += 1
        
        # Entête pour les indicateurs financiers
        row += 1
        summary_sheet.write(row, 0, 'Indicateurs Financiers Clés', header_format)
        summary_sheet.write(row, 1, 'Valeur (Formule Excel)', header_format)
        row += 1
        
        # Feuille 2: Flux de trésorerie détaillés
        cashflow_sheet = workbook.add_worksheet('Flux de Trésorerie')
        cashflow_sheet.set_column('A:A', 15)
        cashflow_sheet.set_column('B:Z', 12)
        
        # Titre de la feuille de flux
        cashflow_sheet.merge_range('A1:E1', f'Analyse des Flux de Trésorerie - Scénario {scenario_name}', title_format)
        
        # En-têtes pour les flux de trésorerie
        headers = ['Année', 'Investissement', 'Revenus', 'OPEX', 'EBITDA', 
                   'Amortissement', 'EBIT', 'Intérêts', 'EBT', 'Impôts', 
                   'Résultat Net', 'Cash Flow', 'FCF Cumulé']
        
        for col, header in enumerate(headers):
            cashflow_sheet.write(2, col, header, header_format)
        
        # Récupérer les données de flux de trésorerie
        cash_flows = scenario_results.get('cash_flows_for_irr_npv', [])
        annual_revenues = scenario_results.get('annual_revenues', [])
        annual_opex = scenario_results.get('annual_opex', [])
        annual_ebitda = scenario_results.get('annual_ebitda', [])
        annual_depreciation = scenario_results.get('annual_depreciation', [])
        annual_ebit = scenario_results.get('annual_ebit', [])
        annual_interest = scenario_results.get('annual_interest', [])
        annual_ebt = scenario_results.get('annual_ebt', [])
        annual_taxes = scenario_results.get('annual_taxes', [])
        annual_net_result = scenario_results.get('annual_net_result', [])
        
        # Nombre d'années
        project_lifetime = len(cash_flows)
        
        # Écrire les données de flux de trésorerie
        for year in range(project_lifetime):
            # Année 0 est l'investissement initial, les années 1+ sont les flux opérationnels
            y = year
            cashflow_sheet.write(3 + year, 0, y, number_format)
            
            # Investissement (seulement à l'année 0)
            if year == 0:
                investment = cash_flows[0] * -1  # Convertir en positif pour l'affichage
                cashflow_sheet.write(3 + year, 1, investment, money_format)
            else:
                cashflow_sheet.write(3 + year, 1, 0, money_format)
            
            # Écrire les valeurs pour chaque année
            if year > 0 and year-1 < len(annual_revenues):
                # Revenus
                cashflow_sheet.write(3 + year, 2, annual_revenues[year-1], money_format)
                # OPEX
                cashflow_sheet.write(3 + year, 3, annual_opex[year-1], money_format)
                # EBITDA
                cashflow_sheet.write(3 + year, 4, annual_ebitda[year-1], money_format)
                # Amortissement
                cashflow_sheet.write(3 + year, 5, annual_depreciation[year-1], money_format)
                # EBIT
                cashflow_sheet.write(3 + year, 6, annual_ebit[year-1], money_format)
                # Intérêts
                cashflow_sheet.write(3 + year, 7, annual_interest[year-1], money_format)
                # EBT
                cashflow_sheet.write(3 + year, 8, annual_ebt[year-1], money_format)
                # Impôts
                cashflow_sheet.write(3 + year, 9, annual_taxes[year-1], money_format)
                # Résultat Net
                cashflow_sheet.write(3 + year, 10, annual_net_result[year-1], money_format)
                # Cash Flow
                cashflow_sheet.write(3 + year, 11, cash_flows[year], money_format)
            else:
                for col in range(2, 12):
                    cashflow_sheet.write(3 + year, col, 0, money_format)
            
            # FCF Cumulé avec formule
            if year == 0:
                cashflow_sheet.write_formula(3 + year, 12, f'=L{4+year}', money_format)
            else:
                cashflow_sheet.write_formula(3 + year, 12, f'=M{3+year}+L{4+year}', money_format)
        
        # Créer des plages pour les formules
        cashflow_range = f'L4:L{3+project_lifetime}'
        cashflow_sheet_name = 'Flux de Trésorerie'
        
        # Écrire les formules pour TRI, VAN et Payback dans la feuille Résumé
        summary_sheet.write(row, 0, 'TRI (IRR)', text_format)
        irr_formula = f'=IRR({cashflow_sheet_name}!{cashflow_range})'
        summary_sheet.write_formula(row, 1, irr_formula, percent_format)
        row += 1
        
        summary_sheet.write(row, 0, 'VAN (NPV)', text_format)
        wacc = scenario_results.get('wacc', 0.05)
        npv_formula = f'=NPV({wacc},{cashflow_sheet_name}!{cashflow_range})'
        summary_sheet.write_formula(row, 1, npv_formula, money_format)
        row += 1
        
        # Formule pour le Payback Period
        summary_sheet.write(row, 0, 'Période de Récupération (Payback)', text_format)
        # Pour le payback, nous utilisons une approximation avec une formule MATCH
        payback_formula = f'=MATCH(TRUE,{cashflow_sheet_name}!M4:M{3+project_lifetime}>=0,0)'
        summary_sheet.write_formula(row, 1, payback_formula, number_format)
        row += 1
        
        # Ajouter des indicateurs additionnels si disponibles
        if scenario_results.get('roi') is not None:
            summary_sheet.write(row, 0, 'ROI', text_format)
            summary_sheet.write(row, 1, scenario_results.get('roi', 0), percent_format)
            row += 1
        
        # Ajouter la formule de ratio de couverture du service de la dette (DSCR)
        if scenario_results.get('avg_dscr') is not None:
            summary_sheet.write(row, 0, 'DSCR Moyen', text_format)
            summary_sheet.write(row, 1, scenario_results.get('avg_dscr', 0), number_format)
            row += 1
        
        # Fermer le workbook et récupérer les bytes
        workbook.close()
        buffer.seek(0)
        return buffer.getvalue()
    
    def display_ppa_cashflow_analysis(self, results, scenario_name):
        """
        Affiche l'analyse des flux de trésorerie PPA
        
        Args:
            results: Tuple contenant (DataFrame d'analyse PPA, métadonnées)
            scenario_name: Nom du scénario utilisé
        """
        if results is None or len(results) != 2:
            st.error("Impossible d'afficher l'analyse des flux de trésorerie PPA")
            return
        
        df_ppa, metadata = results
        
        # Créer un ID unique basé sur le nom du scénario et un timestamp
        unique_id = f"{scenario_name}_{int(time.time()*1000) % 10000}"
        
        st.markdown("### Analyse des flux de trésorerie – PPA")
        st.markdown(f"#### Cashflow – Analyse PPA : Projet photovoltaïque [{scenario_name}]")
        
        # Afficher les métadonnées principales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("VAN", f"{metadata['VAN']:,.2f} €")
        with col2:
            st.metric("TRI", f"{metadata['TRI']:.2f}%" if metadata['TRI'] is not None else "N/A")
        with col3:
            st.metric("Durée d'analyse", f"{metadata['Durée analyse']} ans")
        
        # Afficher le tableau des flux
        st.dataframe(df_ppa.style.format({
            'Investissement initial (CAPEX)': '{:,.2f} €',
            'Subvention': '{:,.2f} €',
            'Production (kWh)': '{:,.2f}',
            'Revenus vente client': '{:,.2f} €',
            'Revenus revente surplus': '{:,.2f} €',
            'Revenus totaux': '{:,.2f} €',
            'Charges exploitation (OPEX)': '{:,.2f} €',
            'Remplacement onduleur': '{:,.2f} €',
            'Démantèlement': '{:,.2f} €',
            'EBITDA': '{:,.2f} €',
            'Intérêts': '{:,.2f} €',
            'Financement': '{:,.2f} €',
            'EBT': '{:,.2f} €',
            'EBT cumulé': '{:,.2f} €'
        }), use_container_width=True)
        
        # Créer un graphique pour visualiser l'évolution des flux
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df_ppa['Année'],
            y=df_ppa['Revenus totaux'],
            name='Revenus totaux',
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            x=df_ppa['Année'],
            y=df_ppa['Charges exploitation (OPEX)'],
            name='OPEX',
            marker_color='red'
        ))
        
        fig.add_trace(go.Scatter(
            x=df_ppa['Année'],
            y=df_ppa['EBITDA'],
            name='EBITDA',
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=df_ppa['Année'],
            y=df_ppa['EBT cumulé'],
            name='EBT cumulé',
            mode='lines+markers',
            line=dict(color='purple', width=2),
            marker=dict(size=6)
        ))
        
        # Ajouter une ligne horizontale à zéro
        fig.add_shape(
            type="line",
            x0=df_ppa['Année'].min(),
            y0=0,
            x1=df_ppa['Année'].max(),
            y1=0,
            line=dict(
                color="black",
                width=2,
                dash="dash",
            )
        )
        
        fig.update_layout(
            title="Évolution des flux financiers PPA",
            xaxis_title="Année",
            yaxis_title="Montant (€)",
            barmode='group',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Utiliser une clé unique pour le graphique
        st.plotly_chart(fig, use_container_width=True, key=f"ppa_chart_{unique_id}")
        
        # Afficher les tableaux détaillés
        with st.expander("Afficher les détails année par année"):
            # Sélection des années à afficher
            selected_year = st.slider("Sélectionner une année spécifique", 0, metadata['Durée analyse'], 0, key=f"year_slider_{unique_id}")
            
            # Afficher les détails pour l'année sélectionnée
            year_data = df_ppa[df_ppa['Année'] == selected_year].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Investissements et Production")
                st.markdown(f"**CAPEX:** {year_data['Investissement initial (CAPEX)']:,.2f} €")
                st.markdown(f"**Subvention:** {year_data['Subvention']:,.2f} €")
                st.markdown(f"**Production:** {year_data['Production (kWh)']:,.2f} kWh")
                
                if year_data['Remplacement onduleur'] > 0:
                    st.markdown(f"**Remplacement onduleur:** {year_data['Remplacement onduleur']:,.2f} €")
                
                if year_data['Démantèlement'] > 0:
                    st.markdown(f"**Coût démantèlement:** {year_data['Démantèlement']:,.2f} €")
            
            with col2:
                st.markdown("#### Revenus")
                st.markdown(f"**Revenus client:** {year_data['Revenus vente client']:,.2f} €")
                st.markdown(f"**Revenus surplus:** {year_data['Revenus revente surplus']:,.2f} €")
                st.markdown(f"**Revenus totaux:** {year_data['Revenus totaux']:,.2f} €")
            
            with col3:
                st.markdown("#### Charges et Résultats")
                st.markdown(f"**OPEX:** {year_data['Charges exploitation (OPEX)']:,.2f} €")
                st.markdown(f"**EBITDA:** {year_data['EBITDA']:,.2f} €")
                st.markdown(f"**Intérêts:** {year_data['Intérêts']:,.2f} €")
                st.markdown(f"**EBT:** {year_data['EBT']:,.2f} €")
                st.markdown(f"**EBT cumulé:** {year_data['EBT cumulé']:,.2f} €")
        
        # Option pour exporter le tableau PPA au format Excel avec mise en forme professionnelle
        with st.expander("Exporter l'analyse financière PPA"):
            if st.button("Créer un fichier Excel professionnel", key=f"excel_button_{unique_id}"):
                # Créer un buffer pour stocker le fichier Excel
                buffer = io.BytesIO()
                
                # Créer un writer Excel avec xlsxwriter pour permettre la mise en forme
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    # Écrire les données dans la feuille Excel
                    df_ppa.to_excel(writer, sheet_name='Analyse PPA', index=False)
                    
                    # Récupérer le classeur et la feuille de calcul
                    workbook = writer.book
                    worksheet = writer.sheets['Analyse PPA']
                    
                    # Définir les formats pour les cellules
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })
                    
                    currency_format = workbook.add_format({
                        'num_format': '# ##0,00 €',
                        'border': 1
                    })
                    
                    number_format = workbook.add_format({
                        'num_format': '# ##0,00',
                        'border': 1
                    })
                    
                    integer_format = workbook.add_format({
                        'num_format': '0',
                        'border': 1
                    })
                    
                    percent_format = workbook.add_format({
                        'num_format': '0.00%',
                        'border': 1
                    })
                    
                    title_format = workbook.add_format({
                        'bold': True,
                        'font_size': 16,
                        'align': 'center',
                        'valign': 'vcenter',
                        'border': 0
                    })
                    
                    subtitle_format = workbook.add_format({
                        'bold': True,
                        'font_size': 12,
                        'align': 'center',
                        'valign': 'vcenter',
                        'border': 0
                    })
                    
                    # Appliquer le format aux en-têtes
                    for col_num, value in enumerate(df_ppa.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Appliquer les formats aux colonnes
                    worksheet.set_column('A:A', 8, integer_format)  # Année
                    worksheet.set_column('B:B', 15, currency_format)  # CAPEX
                    worksheet.set_column('C:C', 15, currency_format)  # Subvention
                    worksheet.set_column('D:D', 15, number_format)    # Production
                    worksheet.set_column('E:E', 15, currency_format)  # Revenus client
                    worksheet.set_column('F:F', 15, currency_format)  # Revenus surplus
                    worksheet.set_column('G:G', 15, currency_format)  # Revenus totaux
                    worksheet.set_column('H:H', 15, currency_format)  # OPEX
                    worksheet.set_column('I:I', 15, currency_format)  # Remplacement onduleur
                    worksheet.set_column('J:J', 15, currency_format)  # Démantèlement
                    worksheet.set_column('K:K', 15, currency_format)  # EBITDA
                    worksheet.set_column('L:L', 15, currency_format)  # Intérêts
                    worksheet.set_column('M:M', 15, currency_format)  # Financement
                    worksheet.set_column('N:N', 15, currency_format)  # EBT
                    worksheet.set_column('O:O', 15, currency_format)  # EBT cumulé
                    
                    # Fusionner des cellules pour le titre et sous-titre
                    worksheet.merge_range('A1:O1', "", title_format)
                    worksheet.merge_range('A2:O2', "", subtitle_format)
                    worksheet.merge_range('A3:O3', "", subtitle_format)
                    
                    # Décaler les données vers le bas pour insérer le titre et les métadonnées
                    worksheet.write('A1', f"Analyse des flux de trésorerie – PPA", title_format)
                    worksheet.write('A2', f"Projet photovoltaïque – {scenario_name}", subtitle_format)
                    worksheet.write('A3', f"VAN: {metadata['VAN']:,.2f} € | TRI: {metadata['TRI']:.2f}% | Durée: {metadata['Durée analyse']} ans", subtitle_format)
                    
                    # Ajouter une feuille de résumé avec les chiffres clés
                    df_summary = pd.DataFrame({
                        'Indicateur': ['VAN', 'TRI', 'Durée d\'analyse', 'CAPEX', 'OPEX année 1', 'Revenus année 1', 'Payback period'],
                        'Valeur': [
                            f"{metadata['VAN']:,.2f} €",
                            f"{metadata['TRI']:.2f}%" if metadata['TRI'] is not None else "N/A",
                            f"{metadata['Durée analyse']} ans",
                            f"{df_ppa['Investissement initial (CAPEX)'].iloc[0]:,.2f} €",
                            f"{df_ppa['Charges exploitation (OPEX)'].iloc[1]:,.2f} €",
                            f"{df_ppa['Revenus totaux'].iloc[1]:,.2f} €",
                            "Calcul en cours..."  # Placeholder pour le calcul du payback
                        ]
                    })
                    
                    # Calculer le payback period
                    payback_year = None
                    for i, row in df_ppa.iterrows():
                        if row['EBT cumulé'] >= 0 and i > 0:  # i > 0 pour ignorer l'année 0
                            # Interpolation pour une estimation plus précise
                            if i > 1 and df_ppa.iloc[i-1]['EBT cumulé'] < 0:
                                last_neg = df_ppa.iloc[i-1]['EBT cumulé']
                                current = row['EBT cumulé']
                                fraction = abs(last_neg) / (current - last_neg)
                                payback_year = row['Année'] - 1 + fraction
                            else:
                                payback_year = row['Année']
                            break
                    
                    # Mettre à jour la valeur du payback period
                    if payback_year is not None:
                        df_summary.loc[df_summary['Indicateur'] == 'Payback period', 'Valeur'] = f"{payback_year:.2f} ans"
                    else:
                        df_summary.loc[df_summary['Indicateur'] == 'Payback period', 'Valeur'] = "Supérieur à 30 ans"
                    
                    # Ajouter la feuille de résumé
                    df_summary.to_excel(writer, sheet_name='Résumé', index=False)
                    summary_sheet = writer.sheets['Résumé']
                    
                    # Formater la feuille de résumé
                    summary_sheet.set_column('A:A', 20)
                    summary_sheet.set_column('B:B', 25)
                    
                    # Ajouter un titre à la feuille de résumé
                    summary_sheet.merge_range('A1:B1', "", title_format)
                    summary_sheet.write('A1', f"Résumé Analyse PPA - {scenario_name}", title_format)
                    
                    # Décaler les données
                    for i, (idx, row) in enumerate(df_summary.iterrows(), start=3):
                        summary_sheet.write(i, 0, row['Indicateur'], header_format)
                        summary_sheet.write(i, 1, row['Valeur'])
                    
                    # Ajouter un graphique dans la feuille Excel
                    chart = workbook.add_chart({'type': 'column'})
                    
                    # Configurer le graphique
                    chart.add_series({
                        'name': 'Revenus totaux',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 6, 4+len(df_ppa)-1, 6],  # Revenus totaux
                        'fill': {'color': 'green'}
                    })
                    
                    chart.add_series({
                        'name': 'OPEX',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 7, 4+len(df_ppa)-1, 7],  # OPEX
                        'fill': {'color': 'red'}
                    })
                    
                    chart.add_series({
                        'name': 'EBITDA',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 10, 4+len(df_ppa)-1, 10],  # EBITDA
                        'type': 'line',
                        'line': {'color': 'blue', 'width': 2.5}
                    })
                    
                    # Configurer les axes et titres
                    chart.set_title({'name': 'Évolution des flux financiers'})
                    chart.set_x_axis({'name': 'Année'})
                    chart.set_y_axis({'name': 'Montant (€)'})
                    
                    # Insérer le graphique
                    chart_sheet = workbook.add_chartsheet('Graphique')
                    chart_sheet.set_chart(chart)
                    
                    # Ajouter un autre graphique pour l'EBT cumulé
                    ebt_chart = workbook.add_chart({'type': 'line'})
                    
                    ebt_chart.add_series({
                        'name': 'EBT cumulé',
                        'categories': ['Analyse PPA', 4, 0, 4+len(df_ppa)-1, 0],  # Années
                        'values': ['Analyse PPA', 4, 14, 4+len(df_ppa)-1, 14],  # EBT cumulé
                        'line': {'color': 'purple', 'width': 2.5},
                        'marker': {'type': 'circle', 'size': 3}
                    })
                    
                    # Ajouter une ligne à zéro
                    ebt_chart.set_y_axis({
                        'name': 'Montant (€)',
                        'major_gridlines': {'visible': True},
                        'line': {'color': 'black'}
                    })
                    
                    ebt_chart.set_title({'name': 'Évolution de l\'EBT cumulé'})
                    ebt_chart.set_x_axis({'name': 'Année'})
                    
                    # Insérer le deuxième graphique
                    worksheet.insert_chart('Q5', ebt_chart, {'x_scale': 1.5, 'y_scale': 1.5})
                
                # Proposer le téléchargement du fichier Excel
                buffer.seek(0)
                
                # Créer un nom de fichier avec le nom du scénario et la date
                today = datetime.now().strftime("%Y-%m-%d")
                filename = f"PPA_Cashflow_{scenario_name}_{today}.xlsx"
                
                st.download_button(
                    label="Télécharger le fichier Excel",
                    data=buffer,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_button_{unique_id}"
                )
    
    def generate_excel_report(self, df_ppa, metadata):
        """
        Génère un rapport Excel complet de l'analyse PPA
        
        Args:
            df_ppa: DataFrame contenant les données de l'analyse PPA
            metadata: Dictionnaire contenant les métadonnées de l'analyse
            
        Returns:
            bytes: Fichier Excel en format binaire
        """
        try:
            # Créer un buffer pour stocker le fichier Excel
            output = BytesIO()
            
            # Créer un writer Excel
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Écrire les données principales
                df_ppa.to_excel(writer, sheet_name='Analyse PPA', index=False)
                
                # Récupérer le workbook et le worksheet
                workbook = writer.book
                worksheet = writer.sheets['Analyse PPA']
                
                # Définir les formats
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D9D9D9',
                    'border': 1
                })
                
                money_format = workbook.add_format({
                    'num_format': '#,##0.00 €',
                    'border': 1
                })
                
                number_format = workbook.add_format({
                    'num_format': '#,##0.00',
                    'border': 1
                })
                
                percent_format = workbook.add_format({
                    'num_format': '0.00%',
                    'border': 1
                })
                
                # Appliquer les formats aux colonnes
                for idx, col in enumerate(df_ppa.columns):
                    # Définir la largeur de colonne
                    worksheet.set_column(idx, idx, 15)
                    
                    # Appliquer le format d'en-tête
                    worksheet.write(0, idx, col, header_format)
                    
                    # Appliquer les formats aux données
                    if 'Année' in col:
                        worksheet.set_column(idx, idx, 8, number_format)
                    elif any(x in col for x in ['Production', 'kWh']):
                        worksheet.set_column(idx, idx, 12, number_format)
                    elif any(x in col for x in ['€', 'CAPEX', 'Revenus', 'OPEX', 'EBITDA', 'EBT']):
                        worksheet.set_column(idx, idx, 15, money_format)
                    else:
                        worksheet.set_column(idx, idx, 12, number_format)
                
                # Créer une feuille pour les métadonnées
                metadata_df = pd.DataFrame([
                    ['Date de l\'analyse', metadata['Date analyse']],
                    ['Scénario', metadata['Scénario']],
                    ['Durée d\'analyse (ans)', metadata['Durée analyse']],
                    ['VAN', metadata['VAN']],
                    ['TRI', metadata['TRI'] if metadata['TRI'] is not None else 'N/A'],
                    ['Taux d\'actualisation', metadata['Taux actualisation'] / 100],
                    ['Production totale (kWh)', metadata['Production totale']],
                    ['Revenus totaux (€)', metadata['Revenus totaux']],
                    ['OPEX total (€)', metadata['OPEX total']]
                ], columns=['Paramètre', 'Valeur'])
                
                metadata_df.to_excel(writer, sheet_name='Métadonnées', index=False)
                
                # Formater la feuille des métadonnées
                worksheet_meta = writer.sheets['Métadonnées']
                worksheet_meta.set_column('A:A', 25)
                worksheet_meta.set_column('B:B', 20)
                
                # Appliquer les formats aux métadonnées
                for idx, (param, value) in enumerate(metadata_df.values, start=1):
                    if 'VAN' in param or 'Revenus' in param or 'OPEX' in param:
                        worksheet_meta.write(idx, 1, value, money_format)
                    elif 'TRI' in param or 'actualisation' in param:
                        if isinstance(value, (int, float)):
                            worksheet_meta.write(idx, 1, value, percent_format)
                        else:
                            worksheet_meta.write(idx, 1, value)
                    elif 'Production' in param:
                        worksheet_meta.write(idx, 1, value, number_format)
                    else:
                        worksheet_meta.write(idx, 1, value)
                
                # Ajouter un graphique
                chart = workbook.add_chart({'type': 'column'})
                
                # Configurer les séries pour le graphique
                chart.add_series({
                    'name': 'Revenus totaux',
                    'categories': ['Analyse PPA', 1, 0, len(df_ppa), 0],
                    'values': ['Analyse PPA', 1, df_ppa.columns.get_loc('Revenus totaux'), len(df_ppa), df_ppa.columns.get_loc('Revenus totaux')],
                    'fill': {'color': '#2E7D32'}
                })
                
                chart.add_series({
                    'name': 'OPEX',
                    'categories': ['Analyse PPA', 1, 0, len(df_ppa), 0],
                    'values': ['Analyse PPA', 1, df_ppa.columns.get_loc('Charges exploitation (OPEX)'), len(df_ppa), df_ppa.columns.get_loc('Charges exploitation (OPEX)')],
                    'fill': {'color': '#C62828'}
                })
                
                # Configurer le graphique
                chart.set_title({'name': 'Évolution des flux financiers PPA'})
                chart.set_x_axis({'name': 'Année'})
                chart.set_y_axis({'name': 'Montant (€)'})
                chart.set_size({'width': 720, 'height': 400})
                
                # Insérer le graphique dans une nouvelle feuille
                worksheet_chart = workbook.add_worksheet('Graphique')
                worksheet_chart.insert_chart('B2', chart)
            
            # Récupérer les données du buffer
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            st.error(f"Erreur lors de la génération du rapport Excel : {str(e)}")
            return None