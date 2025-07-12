import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# Définir les noms des colonnes attendues directement dans ce module
# au lieu de les importer depuis economic_analysis
COLUMN_MAPPINGS = {
    'date': 'Temps',
    'production': 'Énergie PV (CA) déduction faite de la consommation en veille',
    'consumption': 'Consommation'
}

class DataImportModule:
    def __init__(self):
        # Initialiser les structures de données si elles n'existent pas
        if 'production_data' not in st.session_state:
            st.session_state.production_data = None
        
        if 'consumption_data' not in st.session_state:
            st.session_state.consumption_data = None
        
        if 'processed_data' not in st.session_state:
            st.session_state.processed_data = None
        
        if 'data_imported' not in st.session_state:
            st.session_state.data_imported = False
    
    def convert_date_format(self, date_str, year=None):
        """
        Convertit le format de date 'DD.MM. HH:mm' en datetime
        
        Args:
            date_str: String de date au format 'DD.MM. HH:mm'
            year: Année à utiliser (par défaut, année courante)
            
        Returns:
            datetime: Date convertie
        """
        if year is None:
            year = datetime.now().year
            
        try:
            # Ajouter l'année et convertir en datetime
            date_str = str(date_str).strip()
            day, month = date_str.split('.')[0:2]
            hour, minute = date_str.split(' ')[1].split(':')
            
            return datetime(year=year, 
                          month=int(month) if month.strip() else 1,
                          day=int(day),
                          hour=int(hour),
                          minute=int(minute))
        except Exception as e:
            st.error(f"Erreur lors de la conversion de la date '{date_str}': {str(e)}")
            return None
    
    def import_pvsol_data(self, file, file_type):
        """
        Importe les données de production ou de consommation depuis un fichier CSV/Excel de PV*SOL
        
        Args:
            file: Le fichier téléchargé
            file_type: Type de données ('production' ou 'consumption')
            
        Returns:
            DataFrame contenant les données importées
        """
        try:
            file_extension = file.name.split('.')[-1].lower()
            
            # Lire le fichier selon son extension
            if file_extension == 'csv':
                # Essayer plusieurs formats de CSV
                try:
                    # Essai avec le séparateur point-virgule (format européen)
                    df = pd.read_csv(file, sep=';', decimal=',')
                except:
                    try:
                        # Essai avec le séparateur virgule
                        df = pd.read_csv(file, sep=',')
                    except:
                        # Essai avec détection automatique du séparateur
                        df = pd.read_csv(file, sep=None, engine='python')
            elif file_extension in ['xls', 'xlsx']:
                df = pd.read_excel(file, skiprows=18)
            else:
                st.error(f"Format de fichier non supporté : {file_extension}")
                return None
            
            # Détection automatique du format des données en fonction des en-têtes
            if file_type == 'production':
                # Traitement spécifique pour les fichiers de production
                df = self.process_production_data(df)
            else:
                # Traitement spécifique pour les fichiers de consommation
                df = self.process_consumption_data(df)
            
            return df
        
        except Exception as e:
            st.error(f"Erreur lors de l'importation du fichier : {str(e)}")
            return None
    
    def process_production_data(self, df):
        """
        Traite les données de production pour les normaliser
        
        Args:
            df: DataFrame brut importé
            
        Returns:
            DataFrame formaté avec colonnes standardisées
        """
        # Nettoyage des noms de colonnes
        df.columns = [col.strip() for col in df.columns]
        
        # Chercher les colonnes potentielles contenant des données de production
        production_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                                                           ['production', 'energy', 'pv', 'puissance', 'kwh', 'watt'])]
        
        date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                                                    ['date', 'time', 'heure', 'période'])]
        
        # Si des colonnes pertinentes sont trouvées
        if production_cols and date_cols:
            # Sélectionner la première colonne date et production
            date_col = date_cols[0]
            production_col = production_cols[0]
            
            # Créer un nouveau DataFrame normalisé
            result_df = pd.DataFrame()
            result_df['date'] = df[date_col]
            result_df['production_kwh'] = df[production_col]
            
            # Essayer de convertir la colonne date si nécessaire
            try:
                result_df['date'] = pd.to_datetime(result_df['date'])
            except:
                # Si la conversion échoue, conserver la colonne telle quelle
                pass
            
            # Essayer de convertir la production en numérique
            try:
                result_df['production_kwh'] = pd.to_numeric(result_df['production_kwh'].astype(str).str.replace(',', '.'))
            except:
                # Si la conversion échoue, conserver la colonne telle quelle
                pass
            
            return result_df
        
        # Si aucune colonne pertinente n'est trouvée, retourner le DataFrame original
        st.warning("Format de données non reconnu. Utilisez le mode manuel pour sélectionner les colonnes.")
        return df
    
    def process_consumption_data(self, df):
        """
        Traite les données de consommation pour les normaliser
        
        Args:
            df: DataFrame brut importé
            
        Returns:
            DataFrame formaté avec colonnes standardisées
        """
        # Nettoyage des noms de colonnes
        df.columns = [col.strip() for col in df.columns]
        
        # Chercher les colonnes potentielles contenant des données de consommation
        consumption_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                                                           ['consommation', 'consumption', 'load', 'charge', 'kwh', 'watt'])]
        
        date_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in 
                                                    ['date', 'time', 'heure', 'période'])]
        
        # Si des colonnes pertinentes sont trouvées
        if consumption_cols and date_cols:
            # Sélectionner la première colonne date et consommation
            date_col = date_cols[0]
            consumption_col = consumption_cols[0]
            
            # Créer un nouveau DataFrame normalisé
            result_df = pd.DataFrame()
            result_df['date'] = df[date_col]
            result_df['consumption_kwh'] = df[consumption_col]
            
            # Essayer de convertir la colonne date si nécessaire
            try:
                result_df['date'] = pd.to_datetime(result_df['date'])
            except:
                # Si la conversion échoue, conserver la colonne telle quelle
                pass
            
            # Essayer de convertir la consommation en numérique
            try:
                result_df['consumption_kwh'] = pd.to_numeric(result_df['consumption_kwh'].astype(str).str.replace(',', '.'))
            except:
                # Si la conversion échoue, conserver la colonne telle quelle
                pass
            
            return result_df
        
        # Si aucune colonne pertinente n'est trouvée, retourner le DataFrame original
        st.warning("Format de données non reconnu. Utilisez le mode manuel pour sélectionner les colonnes.")
        return df
    
    def create_synthetic_data(self, start_date, periods, production_profile, consumption_profile):
        """
        Crée des données synthétiques pour les tests
        
        Args:
            start_date: Date de début des données
            periods: Nombre de périodes (jours)
            production_profile: Profil de production (type de courbe)
            consumption_profile: Profil de consommation (type de courbe)
            
        Returns:
            (DataFrame de production, DataFrame de consommation)
        """
        # Créer un index de dates
        date_range = pd.date_range(start=start_date, periods=periods, freq='D')
        
        # Créer le DataFrame de production
        production_df = pd.DataFrame()
        production_df['date'] = date_range
        
        # Générer les valeurs de production selon le profil choisi
        if production_profile == 'Sinusoïdal (Saisonnier)':
            # Profil sinusoïdal pour simuler la saisonnalité
            production_df['production_kwh'] = 1000 + 800 * np.sin(np.linspace(0, 2*np.pi, periods))
            # Ajouter du bruit pour plus de réalisme
            production_df['production_kwh'] += np.random.normal(0, 50, periods)
            # Assurer que les valeurs sont positives
            production_df['production_kwh'] = production_df['production_kwh'].clip(lower=0)
        
        elif production_profile == 'Croissant':
            # Profil linéairement croissant
            production_df['production_kwh'] = np.linspace(500, 1500, periods)
            # Ajouter du bruit pour plus de réalisme
            production_df['production_kwh'] += np.random.normal(0, 50, periods)
            # Assurer que les valeurs sont positives
            production_df['production_kwh'] = production_df['production_kwh'].clip(lower=0)
        
        elif production_profile == 'Constant avec variations':
            # Profil constant avec variations aléatoires
            production_df['production_kwh'] = 1000 + np.random.normal(0, 200, periods)
            # Assurer que les valeurs sont positives
            production_df['production_kwh'] = production_df['production_kwh'].clip(lower=0)
        
        # Créer le DataFrame de consommation
        consumption_df = pd.DataFrame()
        consumption_df['date'] = date_range
        
        # Générer les valeurs de consommation selon le profil choisi
        if consumption_profile == 'Sinusoïdal (Saisonnier)':
            # Profil sinusoïdal pour simuler la saisonnalité (pic en hiver)
            consumption_df['consumption_kwh'] = 800 + 400 * np.sin(np.linspace(0, 2*np.pi, periods) + np.pi)
            # Ajouter du bruit pour plus de réalisme
            consumption_df['consumption_kwh'] += np.random.normal(0, 30, periods)
            # Assurer que les valeurs sont positives
            consumption_df['consumption_kwh'] = consumption_df['consumption_kwh'].clip(lower=0)
        
        elif consumption_profile == 'Constant':
            # Profil de consommation constant
            consumption_df['consumption_kwh'] = 800 + np.random.normal(0, 50, periods)
            # Assurer que les valeurs sont positives
            consumption_df['consumption_kwh'] = consumption_df['consumption_kwh'].clip(lower=0)
        
        elif consumption_profile == 'Hebdomadaire':
            # Profil hebdomadaire (bas le weekend, haut en semaine)
            weekday = date_range.dayofweek
            base = 800 * np.ones(periods)
            # Réduire la consommation les weekends (jours 5 et 6)
            base[weekday >= 5] *= 0.7
            consumption_df['consumption_kwh'] = base + np.random.normal(0, 40, periods)
            # Assurer que les valeurs sont positives
            consumption_df['consumption_kwh'] = consumption_df['consumption_kwh'].clip(lower=0)
        
        return production_df, consumption_df
    
    def calculate_autoconsumption(self, production_df, consumption_df):
        """
        Calcule l'autoconsommation et le surplus
        
        Args:
            production_df: DataFrame contenant les données de production
            consumption_df: DataFrame contenant les données de consommation
            
        Returns:
            DataFrame avec les données calculées d'autoconsommation
        """
        # Vérifier que les DataFrames ont une colonne date
        if 'date' not in production_df.columns or 'date' not in consumption_df.columns:
            st.error("Les données n'ont pas de colonne date. Veuillez vérifier le format des fichiers importés.")
            return None
        
        # Convertir les colonnes date en datetime si nécessaire
        if not pd.api.types.is_datetime64_dtype(production_df['date']):
            production_df['date'] = pd.to_datetime(production_df['date'])
        
        if not pd.api.types.is_datetime64_dtype(consumption_df['date']):
            consumption_df['date'] = pd.to_datetime(consumption_df['date'])
        
        # Fusionner les deux DataFrames sur la date
        merged_df = pd.merge(production_df, consumption_df, on='date', how='inner')
        
        # Calculer l'autoconsommation
        merged_df['autoconsumption_kwh'] = merged_df.apply(
            lambda row: min(row['production_kwh'], row['consumption_kwh']), axis=1
        )
        
        # Calculer le surplus (production excédentaire)
        merged_df['surplus_kwh'] = merged_df['production_kwh'] - merged_df['autoconsumption_kwh']
        
        # Calculer le déficit (consommation non couverte par la production)
        merged_df['deficit_kwh'] = merged_df['consumption_kwh'] - merged_df['autoconsumption_kwh']
        
        # Calculer le taux d'autoconsommation
        merged_df['autoconsumption_rate'] = merged_df.apply(
            lambda row: row['autoconsumption_kwh'] / row['production_kwh'] if row['production_kwh'] > 0 else 0, 
            axis=1
        )
        
        # Calculer le taux d'autoproduction
        merged_df['autoproduction_rate'] = merged_df.apply(
            lambda row: row['autoconsumption_kwh'] / row['consumption_kwh'] if row['consumption_kwh'] > 0 else 0, 
            axis=1
        )
        
        return merged_df
    
    def save_processed_data(self, processed_data):
        """
        Sauvegarde les données traitées pour une utilisation ultérieure
        
        Args:
            processed_data: DataFrame contenant les données traitées
            
        Returns:
            bool: True si la sauvegarde a réussi, False sinon
        """
        try:
            # Créer le répertoire data s'il n'existe pas
            if not os.path.exists('data'):
                os.makedirs('data')
            
            # Générer un nom de fichier avec la date et l'heure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/processed_data_{timestamp}.csv"
            
            # Sauvegarder au format CSV
            processed_data.to_csv(filename, index=False)
            
            return True
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde des données : {str(e)}")
            return False
    
    def process_data(self, data):
        """
        Traite les données importées pour les mettre au format attendu
        
        Args:
            data: DataFrame contenant les données brutes
            
        Returns:
            DataFrame: Données traitées
        """
        try:
            # Copie des données pour éviter de modifier l'original
            processed_data = data.copy()
            
            # Vérifier les colonnes requises
            required_columns = ['Date', 'Production (kWh)', 'Consommation (kWh)']
            missing_columns = [col for col in required_columns if col not in processed_data.columns]
            
            if missing_columns:
                st.error(f"Colonnes manquantes dans le fichier : {', '.join(missing_columns)}")
                return None
            
            # Renommer les colonnes pour la standardisation
            column_mapping = {
                'Date': 'date',
                'Production (kWh)': 'production_kwh',
                'Consommation (kWh)': 'consumption_kwh'
            }
            processed_data = processed_data.rename(columns=column_mapping)
            
            # Convertir la colonne date en datetime
            # Essayer différents formats de date courants
            date_formats = [
                '%Y-%m-%d %H:%M:%S',  # Format standard
                '%d/%m/%Y %H:%M',     # Format français
                '%Y-%m-%d %H:%M',     # Format ISO sans secondes
                '%d-%m-%Y %H:%M',     # Format avec tirets
                '%d/%m/%Y %H:%M:%S'   # Format français avec secondes
            ]
            
            date_converted = False
            for date_format in date_formats:
                try:
                    processed_data['date'] = pd.to_datetime(processed_data['date'], format=date_format)
                    date_converted = True
                    break
                except:
                    continue
            
            if not date_converted:
                st.error("Impossible de convertir la colonne date. Veuillez vérifier le format de date dans votre fichier.")
                return None
            
            # Trier les données par date
            processed_data = processed_data.sort_values('date')
            
            # Vérifier que les données sont au pas horaire
            time_diff = processed_data['date'].diff().median()
            if time_diff != pd.Timedelta(hours=1):
                st.warning(f"Les données ne semblent pas être au pas horaire (différence médiane : {time_diff}). Le traitement continue mais les résultats pourraient être affectés.")
            
            # Convertir les colonnes numériques en float
            numeric_columns = ['production_kwh', 'consumption_kwh']
            for col in numeric_columns:
                processed_data[col] = pd.to_numeric(processed_data[col], errors='coerce')
            
            # Vérifier les valeurs manquantes
            if processed_data[numeric_columns].isna().any().any():
                st.warning("Certaines valeurs sont manquantes dans les données. Elles seront remplacées par 0.")
                processed_data[numeric_columns] = processed_data[numeric_columns].fillna(0)
            
            # Vérifier les valeurs négatives
            if (processed_data[numeric_columns] < 0).any().any():
                st.warning("Certaines valeurs sont négatives. Elles seront remplacées par 0.")
                processed_data[numeric_columns] = processed_data[numeric_columns].clip(lower=0)
            
            return processed_data
            
        except Exception as e:
            st.error(f"Erreur lors du traitement des données : {str(e)}")
            return None
    
    def show_ui(self):
        """Affiche l'interface utilisateur du module d'importation"""
        st.markdown("<h1 class='main-header'>Importation des Données</h1>", unsafe_allow_html=True)

        # Initialiser le dictionnaire pour stocker les données des sites s'il n'existe pas
        if 'sites_data' not in st.session_state:
            st.session_state.sites_data = {}
        if 'data_imported' not in st.session_state:
             st.session_state.data_imported = False # S'assurer que cet état existe aussi
        
        # Afficher l'interface d'importation de fichier PVSOL
        st.markdown("<h3 class='sub-header'>Importation Fichiers PVSOL (Multi-sites)</h3>", unsafe_allow_html=True)
        
        # Uploader pour les fichiers PVSOL (accepte plusieurs fichiers)
        pvsol_files = st.file_uploader(
            "Importer un ou plusieurs fichiers Excel de PVSOL (un par site)",
            type=['xlsx', 'xls'],
            accept_multiple_files=True, # <-- Permet l'upload multiple
            key="pvsol_excel_uploader"
        )
        
        if pvsol_files: # Si au moins un fichier est chargé
             st.markdown("---")
             st.markdown("### Fichiers Chargés :")
             
             # Boucler sur chaque fichier chargé
             for uploaded_file in pvsol_files:
                  site_id = uploaded_file.name # Utiliser le nom du fichier comme ID
                  st.markdown(f"#### Traitement pour : `{site_id}`")

                  # Vérifier si ce site a déjà été traité pour éviter de le refaire inutilement
                  # Ou laisser l'utilisateur re-traiter s'il le souhaite
                  # if site_id in st.session_state.sites_data:
                  #      st.info(f"Le site '{site_id}' a déjà été traité. Pour le re-traiter, supprimez-le d'abord ci-dessous.")
                  #      continue # Passer au fichier suivant

                  try:
                      # Lire le contenu du fichier en mémoire
                      file_content = uploaded_file.read()
                      
                      # Utiliser BytesIO pour lire le fichier Excel
                      with io.BytesIO(file_content) as bio:
                          # Lecture des noms de colonnes (première ligne)
                          df_headers = pd.read_excel(bio, nrows=1, engine='openpyxl')
                          
                          # Réinitialiser le pointeur du fichier
                          bio.seek(0)
                          
                          # Lecture du fichier Excel en commençant à la ligne 19
                          df_pvsol = pd.read_excel(bio, skiprows=18, engine='openpyxl')
                          
                          # Utiliser les noms de colonnes de la première ligne
                          column_names = df_headers.columns.tolist()
                          df_pvsol.columns = column_names
                      
                      st.success(f"Fichier `{site_id}` lu avec succès.")
                      
                      # Afficher un aperçu des données brutes
                      with st.expander(f"Voir Aperçu Données Brutes pour `{site_id}`"):
                           st.dataframe(df_pvsol.head())
                      
                      # Interface de mapping des colonnes pour ce fichier spécifique
                      st.markdown("##### Configuration du mapping des colonnes")
                      available_columns = df_pvsol.columns.tolist()
                      
                      # Définir les colonnes prioritaires pour chaque type
                      date_columns_priority = ["Temps", "Date", "DateTime", "Time"]
                      production_columns_priority = ["Énergie PV (CC)", "Production PV", "Énergie PV", "Production", "PV Energy"]
                      consumption_columns_priority = ["Consommation", "Consumption", "Load"]

                      # Initialiser les index par défaut
                      date_index = 0
                      prod_index = 0
                      cons_index = 0

                      # Fonction pour trouver l'index d'une colonne en utilisant une liste de priorités
                      # (Cette fonction peut être sortie de la boucle si elle est toujours la même)
                      def find_column_index(columns, priority_list):
                          # D'abord rechercher les correspondances exactes
                          for priority in priority_list:
                              if priority in columns:
                                  return columns.index(priority)
                          
                          # Ensuite rechercher les correspondances partielles
                          for priority in priority_list:
                              for i, col in enumerate(columns):
                                  if priority.lower() in col.lower():
                                      return i
                          
                          # Si aucune correspondance, retourner un index par défaut
                          if len(columns) > 0:
                              return 0
                          return None


                      # Trouver les index par défaut en utilisant la liste de priorités
                      date_index = find_column_index(available_columns, date_columns_priority)
                      prod_index = find_column_index(available_columns, production_columns_priority)
                      cons_index = find_column_index(available_columns, consumption_columns_priority)

                      # Éviter les doublons (logique existante)
                      if prod_index == date_index and len(available_columns) > 1:
                           candidates = [i for i in range(len(available_columns)) if i != date_index]
                           if candidates: prod_index = candidates[0]

                      if cons_index == date_index or cons_index == prod_index:
                           if len(available_columns) > 2:
                                candidates = [i for i in range(len(available_columns)) if i != date_index and i != prod_index]
                                if candidates: cons_index = candidates[0]

                      # Fallback (logique existante)
                      if date_index is None: date_index = 0
                      if prod_index is None: prod_index = min(1, len(available_columns)-1) if len(available_columns) > 1 else 0
                      if cons_index is None: cons_index = min(2, len(available_columns)-1) if len(available_columns) > 2 else prod_index

                      # Vérification finale (logique existante)
                      date_index = min(date_index, len(available_columns)-1) if available_columns else 0
                      prod_index = min(prod_index, len(available_columns)-1) if available_columns else 0
                      cons_index = min(cons_index, len(available_columns)-1) if available_columns else 0

                      # Créer les sélecteurs de colonnes avec des clés uniques par fichier
                      # Utiliser site_id dans la clé pour les rendre uniques
                      key_prefix = f"map_{site_id}" 
                      col1, col2, col3 = st.columns(3)

                      with col1:
                          date_col = st.selectbox(
                              "Colonne Date/Heure", options=available_columns, index=date_index,
                              key=f"{key_prefix}_date_col"
                          )

                      with col2:
                          prod_col = st.selectbox(
                              "Colonne Production PV", options=available_columns, index=prod_index,
                              key=f"{key_prefix}_prod_col"
                          )

                      with col3:
                          cons_col = st.selectbox(
                              "Colonne Consommation", options=available_columns, index=cons_index,
                              key=f"{key_prefix}_cons_col"
                          )
                      
                      # Bouton de traitement pour ce fichier spécifique
                      if date_col is not None and prod_col is not None and cons_col is not None:
                          # Clé unique pour le bouton
                          if st.button(f"Traiter et Stocker Données pour `{site_id}`", key=f"process_{site_id}"):
                              with st.spinner(f"Traitement des données pour '{site_id}' en cours..."):
                                  try:
                                      # Créer un DataFrame avec les colonnes mappées et les noms standardisés
                                      # Note: S'assurer que prod_col et cons_col existent bien dans df_pvsol
                                      data_dict = {'Temps': df_pvsol[date_col]}
                                      if prod_col in df_pvsol:
                                           data_dict['production_kwh'] = df_pvsol[prod_col]
                                      if cons_col in df_pvsol:
                                           data_dict['consumption_kwh'] = df_pvsol[cons_col]
                                      
                                      processed_df = pd.DataFrame(data_dict)
                                      
                                      # --- DEBUT BLOC STANDARDISATION --- 
                                      # Assurer la présence et le type correct de la colonne Temps
                                      if 'Temps' not in processed_df.columns:
                                          # Ceci ne devrait pas arriver si date_col est valide, mais par sécurité
                                          raise ValueError("La colonne 'Temps' mappée est manquante.") 
                                      # Appliquer la conversion de date (si ce n'est pas déjà fait)
                                      try:
                                           processed_df['Temps'] = processed_df['Temps'].apply(lambda x: self.convert_date_format(x))
                                           # Vérifier les NaT après conversion
                                           if processed_df['Temps'].isnull().any():
                                                raise ValueError("La conversion de date a produit des valeurs nulles (vérifiez le format dd.mm hh:mm).")
                                      except Exception as e_conv_date:
                                           st.error(f"Erreur conversion date pour {site_id}: {e_conv_date}")
                                           # Essayer pd.to_datetime comme fallback
                                           try:
                                                processed_df['Temps'] = pd.to_datetime(processed_df['Temps'], errors='coerce')
                                                if processed_df['Temps'].isnull().any():
                                                     raise ValueError("Échec de la conversion de la colonne 'Temps' en datetime (formats essayés: dd.mm hh:mm, standard).")
                                           except Exception as e_conv_dt:
                                                raise ValueError(f"Échec final conversion date pour {site_id}: {e_conv_dt}") from e_conv_dt

                                      # Assurer la présence de 'production_kwh', remplir avec 0 si absente
                                      if 'production_kwh' not in processed_df.columns:
                                          st.warning(f"Colonne production non trouvée/mappée pour {site_id}. Site considéré comme consommateur pur.")
                                          processed_df['production_kwh'] = 0.0
                                      else:
                                          processed_df['production_kwh'] = pd.to_numeric(processed_df['production_kwh'], errors='coerce').fillna(0.0)
                                          processed_df['production_kwh'] = processed_df['production_kwh'].clip(lower=0) # Assurer > 0

                                      # Assurer la présence de 'consumption_kwh', remplir avec 0 si absente
                                      if 'consumption_kwh' not in processed_df.columns:
                                          st.warning(f"Colonne consommation non trouvée/mappée pour {site_id}. Site considéré comme producteur pur (ou données manquantes).")
                                          processed_df['consumption_kwh'] = 0.0
                                      else:
                                          processed_df['consumption_kwh'] = pd.to_numeric(processed_df['consumption_kwh'], errors='coerce').fillna(0.0)
                                          processed_df['consumption_kwh'] = processed_df['consumption_kwh'].clip(lower=0) # Assurer > 0

                                      # Sélectionner et ordonner les colonnes finales, trier par Temps et supprimer lignes avec Temps NaN
                                      processed_df = processed_df[['Temps', 'production_kwh', 'consumption_kwh']].sort_values(by='Temps').dropna(subset=['Temps'])
                                      # --- FIN BLOC STANDARDISATION --- 

                                      # Supprimer l'ancien calcul redondant d'autoconsommation ici
                                      # processed_df = processed_df.dropna(subset=['Temps', 'production_kwh', 'consumption_kwh'])
                                      
                                      # Stocker les résultats dans le dictionnaire sites_data
                                      # Initialiser si nécessaire
                                      if 'sites_data' not in st.session_state:
                                           st.session_state.sites_data = {}
                                      st.session_state.sites_data[site_id] = processed_df
                                      st.session_state.data_imported = True # Indiquer qu'au moins un site est importé
                                      
                                      st.success(f"Données pour le site '{site_id}' traitées et standardisées.")

                                      # Forcer un re-rendu pour mettre à jour la liste des sites importés ci-dessous
                                      st.rerun() 
                                      
                                  except Exception as e:
                                      st.error(f"Erreur lors du traitement des données pour '{site_id}': {str(e)}")
                      else:
                           st.warning(f"Vérifiez que les colonnes Date, Production et Consommation sont correctement sélectionnées pour `{site_id}`.")

                  except Exception as e:
                      st.error(f"Erreur lors de la lecture du fichier `{site_id}` : {str(e)}")

                  st.markdown("---") # Séparateur entre les fichiers

        # Afficher les sites importés (en dehors de la boucle d'upload)
        if st.session_state.sites_data:
            st.markdown("---")
            st.markdown("### Sites Actuellement Importés :")
            
            sites_list = list(st.session_state.sites_data.keys())
            cols = st.columns(len(sites_list)) # Une colonne par site pour les boutons de suppression
            
            for i, site_id in enumerate(sites_list):
                site_df = st.session_state.sites_data[site_id]
                # Afficher info et bouton supprimer dans sa colonne
                with cols[i]:
                    st.write(f"**{site_id}**")
                    st.caption(f"{len(site_df)} lignes")
                    if st.button(f"Supprimer {site_id}", key=f"delete_{site_id}", help="Supprimer les données de ce site"):
                        del st.session_state.sites_data[site_id]
                        # Mettre à jour data_imported si plus aucun site n'est présent
                        if not st.session_state.sites_data:
                            st.session_state.data_imported = False
                        st.rerun() # Recharger pour mettre à jour l'affichage

            # Ajouter un bouton pour vider tous les sites si nécessaire
            if len(st.session_state.sites_data) > 1: # Optionnel: montrer seulement si > 1 site
                 st.markdown("---") # Séparateur visuel
                 if st.button("Réinitialiser Tous les Sites Importés"):
                      st.session_state.sites_data = {}
                      st.session_state.data_imported = False
                      st.rerun()
        else:
             st.info("Aucun site importé pour le moment. Utilisez le bouton ci-dessus pour charger les fichiers.")