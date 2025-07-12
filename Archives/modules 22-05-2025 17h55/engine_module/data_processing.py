# modules/engine_module/data_processing.py
import pandas as pd
import numpy as np
import logging
from datetime import datetime # Assurez-vous que datetime est importé

logger = logging.getLogger(__name__)

def validate_and_prepare_sites_data(sites_data_input: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Valide les données de chaque site, convertit 'Temps' en datetime,
    et s'assure que les colonnes 'production_kwh' et 'consumption_kwh' existent (avec 0.0 par défaut).
    """
    logger.info("DÉBUT validate_and_prepare_sites_data")
    processed_sites_data = {}
    if not isinstance(sites_data_input, dict):
        logger.error("sites_data_input doit être un dictionnaire.")
        return processed_sites_data

    logger.info(f"Nombre de sites à traiter: {len(sites_data_input)}")
    logger.info(f"IDs des sites: {list(sites_data_input.keys())}")
    
    for site_id, df_site_init in sites_data_input.items():
        logger.info(f"Traitement du site '{site_id}'")
        if not isinstance(df_site_init, pd.DataFrame) or df_site_init.empty:
            logger.warning(f"DataFrame vide ou invalide pour le site '{site_id}'. Ce site sera ignoré.")
            continue
        
        df_copy = df_site_init.copy()
        logger.info(f"Site '{site_id}' - Shape initial: {df_copy.shape}")
        logger.info(f"Site '{site_id}' - Colonnes initiales: {df_copy.columns.tolist()}")

        if not df_copy.empty:
            if 'Temps' not in df_copy.columns:
                logger.error(f"Colonne 'Temps' manquante pour le site '{site_id}'. Ce site sera ignoré.")
                continue
            try:
                if not pd.api.types.is_datetime64_any_dtype(df_copy['Temps']):
                    logger.info(f"Site '{site_id}' - Tentative de conversion de 'Temps' en datetime")
                    
                    # Tentative de récupérer l'année de début du projet depuis la config globale.
                    # Ceci est une supposition sur la disponibilité de st.session_state ici.
                    # Si ce script n'est pas exécuté dans un contexte Streamlit avec st.session_state.config,
                    # il faudra une autre méthode pour passer/accéder à la config globale.
                    # Pour l'instant, on garde un fallback sur l'année actuelle.
                    start_year_for_data = datetime.now().year # Année par défaut
                    # try:
                    #     # Tenter de récupérer l'année de début PPA si la config est accessible
                    #     # Cette partie est hypothétique car l'accès direct à st.session_state.config
                    #     # depuis ce module peut ne pas être garanti.
                    #     # Il serait préférable de passer 'config' en argument si nécessaire.
                    #     if 'st' in sys.modules and hasattr(st, 'session_state') and 'config' in st.session_state:
                    #         date_debut_ppa_str = st.session_state.config.get("date_debut_ppa")
                    #         if date_debut_ppa_str:
                    #             start_year_for_data = pd.to_datetime(date_debut_ppa_str).year
                    #             logger.info(f"Utilisation de l'année {start_year_for_data} (depuis config date_debut_ppa) pour les données de '{site_id}'.")
                    # except Exception:
                    #     logger.warning(f"Impossible de récupérer l'année de début PPA depuis la config pour '{site_id}'. Utilisation de l'année actuelle ({start_year_for_data}).")


                    def convert_custom_time_format(time_val):
                        if isinstance(time_val, (datetime, pd.Timestamp)):
                            return time_val
                        try:
                            # Essayer le format "DD.MM. HH:MM" ou "DD.MM.YY HH:MM" ou "DD.MM.YYYY HH:MM"
                            # et aussi "DD/MM/..."
                            time_str = str(time_val).replace('/', '.') # Homogénéiser les séparateurs de date
                            
                            # Vérifier si le format contient explicitement une année (YY ou YYYY) après DD.MM.
                            parts = time_str.split(' ') # Sépare la date de l'heure
                            date_parts_dots = parts[0].split('.')
                            
                            if len(date_parts_dots) == 3 and len(date_parts_dots[2]) in [2,4]: # DD.MM.YY ou DD.MM.YYYY
                                # L'année est déjà présente, laissons pd.to_datetime gérer
                                return pd.to_datetime(time_str, dayfirst=True, errors='coerce')

                            # Si seulement DD.MM. HH:MM
                            if len(date_parts_dots) == 2 or (len(date_parts_dots) == 3 and not date_parts_dots[2]): # DD.MM. ou DD.MM
                                date_part_val = parts[0]
                                time_part_val = parts[1] if len(parts) > 1 else "00:00"
                                day, month = map(int, date_part_val.split('.')[0:2])
                                hour, minute = map(int, time_part_val.split(':')[0:2])
                                
                                # Utiliser l'année déterminée (potentiellement depuis config ou année actuelle)
                                converted_date = datetime(start_year_for_data, month, day, hour, minute)
                                # logger.debug(f"Custom conversion for '{time_val}' to '{converted_date}' using year {start_year_for_data}")
                                return converted_date
                        except Exception:
                            # Si le format custom échoue, pd.to_datetime essaiera d'autres formats
                            # logger.debug(f"Custom format failed for '{time_val}', falling back to pd.to_datetime default.")
                            pass # Laisser pd.to_datetime essayer
                        
                        # Tentative finale avec pd.to_datetime, en essayant dayfirst=True
                        # si le format n'a pas été attrapé par la logique custom.
                        dt_obj = pd.to_datetime(time_val, errors='coerce', dayfirst=True)
                        if pd.isna(dt_obj): # Si échec, essayer sans dayfirst
                            dt_obj = pd.to_datetime(time_val, errors='coerce')
                        return dt_obj

                    df_copy['Temps'] = df_copy['Temps'].apply(convert_custom_time_format)
                    
                    if df_copy['Temps'].isnull().any():
                        logger.error(f"La conversion de 'Temps' en datetime a produit des NaT pour le site '{site_id}' après tentatives. Vérifiez le format. Ce site sera ignoré.")
                        processed_sites_data[site_id] = pd.DataFrame() # Renvoyer un DF vide pour ce site
                        continue 
                
                if not pd.api.types.is_datetime64_any_dtype(df_copy['Temps']):
                    logger.error(f"La colonne 'Temps' pour le site '{site_id}' n'a pas pu être convertie en type datetime valide. Ce site sera ignoré.")
                    processed_sites_data[site_id] = pd.DataFrame()
                    continue

            except Exception as e_time: 
                logger.error(f"Format de la colonne 'Temps' invalide ou erreur de conversion majeure pour le site '{site_id}': {e_time}. Ce site sera ignoré.", exc_info=True)
                processed_sites_data[site_id] = pd.DataFrame()
                continue

            for col in ['production_kwh', 'consumption_kwh']:
                if col not in df_copy.columns:
                    logger.info(f"Colonne '{col}' manquante site '{site_id}'. Ajout avec zéros.")
                    df_copy[col] = 0.0
                try:
                    logger.info(f"Site '{site_id}' - Conversion de '{col}' en numérique")
                    # Afficher quelques valeurs avant conversion
                    if not df_copy.empty:
                        logger.info(f"Site '{site_id}' - Échantillon '{col}' avant conversion: {df_copy[col].head().tolist()}")
                    
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').fillna(0.0)
                    
                    # Afficher stats après conversion
                    sum_val = df_copy[col].sum()
                    logger.info(f"Site '{site_id}' - Somme '{col}' après conversion: {sum_val:.2f}")
                    if col == 'production_kwh' and sum_val < 1.0:
                        logger.warning(f"⚠️ ALERTE: Site '{site_id}' - Production totale quasi nulle ({sum_val:.2f})!")
                    
                except Exception as e_num: 
                    logger.error(f"Impossible de convertir la colonne '{col}' en numérique pour le site '{site_id}': {e_num}. Mise à 0.")
                    df_copy[col] = 0.0
            processed_sites_data[site_id] = df_copy
            logger.info(f"Site '{site_id}' - Ajouté aux données préparées avec shape: {df_copy.shape}")
        else:
            processed_sites_data[site_id] = df_copy # Stocker le DataFrame vide s'il l'était initialement
            logger.info(f"Données vides pour le site '{site_id}'.")
    
    logger.info(f"FIN validate_and_prepare_sites_data - Nombre de sites préparés: {len(processed_sites_data)}")
    for site_id, df in processed_sites_data.items():
        prod_sum = df['production_kwh'].sum() if 'production_kwh' in df.columns else 0.0
        cons_sum = df['consumption_kwh'].sum() if 'consumption_kwh' in df.columns else 0.0
        logger.info(f"Site '{site_id}' - Somme production: {prod_sum:.2f}, Somme consommation: {cons_sum:.2f}")
            
    return processed_sites_data

def aggregate_energy_data(processed_sites_data: dict[str, pd.DataFrame], 
                            effective_sites_config: dict | None = None) -> pd.DataFrame:
    """
    Agrège les données de production et de consommation de tous les sites valides.
    Prend en compte le type de site ("Consommateur Pur") pour la production.
    Retourne un DataFrame avec les colonnes 'Temps', 'production_kwh', 'consumption_kwh'.
    """
    logger.info("DÉBUT aggregate_energy_data")
    
    if not processed_sites_data or not any(not df.empty for df in processed_sites_data.values()):
        logger.warning("Aucune donnée de site énergétique valide à agréger. Retour d'un DataFrame vide.")
        # Créer un DataFrame vide avec les colonnes attendues pour la cohérence
        return pd.DataFrame(columns=['Temps', 'production_kwh', 'consumption_kwh'])

    all_dfs_valid = [df for df in processed_sites_data.values() if not df.empty and 'Temps' in df.columns]
    logger.info(f"Nombre de DataFrames valides pour agrégation: {len(all_dfs_valid)}")
    
    if not all_dfs_valid:
        logger.warning("Aucun DataFrame de site valide (avec colonne 'Temps') pour l'agrégation.")
        return pd.DataFrame(columns=['Temps', 'production_kwh', 'consumption_kwh'])

    # Loguer les sommes de production et consommation par site
    for site_id, df in processed_sites_data.items():
        if not df.empty and 'Temps' in df.columns:
            prod_sum = df['production_kwh'].sum() if 'production_kwh' in df.columns else 0.0
            cons_sum = df['consumption_kwh'].sum() if 'consumption_kwh' in df.columns else 0.0
            logger.info(f"Site '{site_id}' - Somme production avant agrégation: {prod_sum:.2f}, Somme consommation: {cons_sum:.2f}")
            
            # Afficher le type de site si disponible
            site_cfg = (effective_sites_config or {}).get(site_id, {})
            site_type = site_cfg.get('site_type', 'Producteur')
            logger.info(f"Site '{site_id}' - Type: {site_type}")

    min_date_list = [df['Temps'].min() for df in all_dfs_valid if not df['Temps'].empty]
    max_date_list = [df['Temps'].max() for df in all_dfs_valid if not df['Temps'].empty]

    if not min_date_list or not max_date_list:
        logger.warning("Impossible de déterminer les dates min/max des données de site valides.")
        return pd.DataFrame(columns=['Temps', 'production_kwh', 'consumption_kwh'])
    
    min_date = min(min_date_list)
    max_date = max(max_date_list)
    logger.info(f"Plage de dates pour l'agrégation: {min_date} à {max_date}")
    
    freq = 'H' # Fréquence par défaut
    first_df_non_empty_for_freq = all_dfs_valid[0]
    temp_times = pd.to_datetime(first_df_non_empty_for_freq['Temps'], errors='coerce').dropna().sort_values()

    if not temp_times.empty:
        inferred_freq = pd.infer_freq(temp_times)
        if inferred_freq: 
            freq = inferred_freq
            logger.info(f"Fréquence inférée des données: {freq}")
        else: 
            time_diffs = temp_times.diff().dropna()
            if not time_diffs.empty:
                median_diff = time_diffs.median()
                try:
                    offset_freq = pd.tseries.frequencies.to_offset(median_diff)
                    if offset_freq: 
                        freq = offset_freq
                        logger.info(f"Fréquence déterminée à partir de la différence médiane: {freq}")
                except ValueError:
                     logger.warning(f"Impossible de convertir la différence de temps médiane '{median_diff}' en offset de fréquence. Utilisation de 'H'.")
    
    try:
        common_index = pd.date_range(start=min_date, end=max_date, freq=freq)
        logger.info(f"Index commun créé avec {len(common_index)} points de temps")
    except ValueError as e_dr:
        logger.error(f"Erreur lors de la création de common_index (freq={freq}, min={min_date}, max={max_date}): {e_dr}. Tentative avec freq=None.")
        try:
            common_index = pd.date_range(start=min_date, end=max_date, freq=None) # Laisser pandas déduire si possible
            logger.info(f"Nouvel essai common_index avec freq=None. Longueur: {len(common_index)}")
        except Exception as e_dr_fallback:
            logger.critical(f"Échec final de création de common_index: {e_dr_fallback}")
            return pd.DataFrame(columns=['Temps', 'production_kwh', 'consumption_kwh'])


    if common_index.empty :
        logger.warning(f"L'index commun (common_index) est vide (freq={freq}, min={min_date}, max={max_date}). Vérifiez les données de temps des sites.")
        return pd.DataFrame(columns=['Temps', 'production_kwh', 'consumption_kwh'])

    data_agg_df = pd.DataFrame(0.0, index=common_index, columns=['production_kwh', 'consumption_kwh'])
    logger.info(f"DataFrame d'agrégation initial créé avec shape: {data_agg_df.shape}")
    
    for site_id, df_site_validated in processed_sites_data.items():
        if df_site_validated.empty or 'Temps' not in df_site_validated.columns:
            logger.info(f"Site '{site_id}' ignoré pour l'agrégation (vide ou sans 'Temps')")
            continue
        
        logger.info(f"Agrégation du site '{site_id}' - Shape: {df_site_validated.shape}")
        
        site_cfg = (effective_sites_config or {}).get(site_id, {})
        site_type = site_cfg.get('site_type', 'Producteur') # Par défaut Producteur si non spécifié
        logger.info(f"Site '{site_id}' - Type: {site_type}")
        
        df_temp_site = df_site_validated.set_index('Temps')
        if df_temp_site.index.has_duplicates:
            logger.info(f"Agrégation des doublons de temps pour le site {site_id}.")
            df_temp_site = df_temp_site.groupby(df_temp_site.index).sum()
        
        # Assurer la présence des colonnes et appliquer la logique pour consommateur pur
        if 'consumption_kwh' not in df_temp_site.columns: 
            logger.info(f"Site '{site_id}' - Ajout colonne 'consumption_kwh' manquante avec zéros")
            df_temp_site['consumption_kwh'] = 0.0
        
        if site_type == "Consommateur Pur":
            logger.info(f"Site '{site_id}' - Site consommateur pur: production forcée à 0")
            df_temp_site['production_kwh'] = 0.0 # Forcer la production à 0
        elif 'production_kwh' not in df_temp_site.columns:
            logger.info(f"Site '{site_id}' - Ajout colonne 'production_kwh' manquante avec zéros")
            df_temp_site['production_kwh'] = 0.0
        
        # Loguer la somme avant reindex
        prod_sum_before = df_temp_site['production_kwh'].sum()
        cons_sum_before = df_temp_site['consumption_kwh'].sum()
        logger.info(f"Site '{site_id}' - Avant reindex: production={prod_sum_before:.2f}, consommation={cons_sum_before:.2f}")
        
        df_temp_reindexed_site = df_temp_site[['production_kwh', 'consumption_kwh']].reindex(common_index, fill_value=0.0)
        
        # Loguer la somme après reindex
        prod_sum_after = df_temp_reindexed_site['production_kwh'].sum()
        cons_sum_after = df_temp_reindexed_site['consumption_kwh'].sum()
        logger.info(f"Site '{site_id}' - Après reindex: production={prod_sum_after:.2f}, consommation={cons_sum_after:.2f}")
        
        # Vérifier si les sommes sont conservées après reindex
        if abs(prod_sum_before - prod_sum_after) > 0.01:
            logger.warning(f"⚠️ Site '{site_id}' - La somme de production a changé après reindex: {prod_sum_before:.2f} -> {prod_sum_after:.2f}")
        
        # Somme avant addition
        prod_sum_agg_before = data_agg_df['production_kwh'].sum()
        
        data_agg_df = data_agg_df.add(df_temp_reindexed_site, fill_value=0.0)
        
        # Somme après addition
        prod_sum_agg_after = data_agg_df['production_kwh'].sum()
        logger.info(f"Somme de production agrégée: {prod_sum_agg_before:.2f} -> {prod_sum_agg_after:.2f} (après ajout du site '{site_id}')")
            
    # Vérification finale
    final_prod_sum = data_agg_df['production_kwh'].sum()
    final_cons_sum = data_agg_df['consumption_kwh'].sum()
    logger.info(f"Résultat final d'agrégation - Shape: {data_agg_df.shape}")
    logger.info(f"Résultat final d'agrégation - Somme production: {final_prod_sum:.2f}, Somme consommation: {final_cons_sum:.2f}")
    
    if final_prod_sum < 1.0:
        logger.error(f"⚠️ ALERTE CRITIQUE: Production totale agrégée quasi nulle ({final_prod_sum:.2f})!")
    
    result_df = data_agg_df.reset_index().rename(columns={'index': 'Temps'})
    logger.info(f"FIN aggregate_energy_data - DataFrame final avec shape: {result_df.shape}")
    
    return result_df