#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse des prospects solaires - Département 06 (Export CSV direct)

CONTEXTE : Prospection solaire / autoconsommation collective
Objectif : Analyser les prospects basés sur l'export CSV Enedis

Auteur : OptimPV
Date : 2024
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import warnings

import pandas as pd
import requests

warnings.filterwarnings('ignore')

# === CONFIGURATION =============================================================
CONFIG = {
    'URLS': {
        # URL d'export CSV direct
        'CSV_EXPORT': 'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/exports/csv'
    },
    'DEPARTEMENT': '06',
    'SEUIL_CONSO_DEFAULT': 7.0,  # En MWh (équivalent à 7000 kWh)
    'DATA_DIR': './data'
}

# === LOGGING ===================================================================
def setup_logging() -> logging.Logger:
    """Configure le système de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('prospects_06.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# === FONCTIONS PRINCIPALES ====================================================
def create_data_directory() -> Path:
    """Crée le répertoire de données s'il n'existe pas."""
    data_dir = Path(CONFIG['DATA_DIR'])
    data_dir.mkdir(exist_ok=True)
    return data_dir

def download_csv_data(data_dir: Path) -> pd.DataFrame:
    """Télécharge le fichier CSV complet depuis Enedis."""
    csv_file = data_dir / 'enedis_consommation_complete.csv'
    
    # Vérifier si le fichier existe déjà
    if csv_file.exists():
        logger.info(f"Fichier CSV existant trouvé : {csv_file}")
        logger.info("Chargement du fichier existant...")
        df = pd.read_csv(csv_file, encoding='utf-8', sep=';')
        logger.info(f"Données chargées : {len(df)} enregistrements")
        return df
    
    logger.info("Téléchargement du fichier CSV complet depuis Enedis...")
    logger.info("⚠️  Attention : Ce téléchargement peut prendre plusieurs minutes...")
    
    try:
        # Télécharger le CSV complet
        response = requests.get(CONFIG['URLS']['CSV_EXPORT'], timeout=300)  # 5 minutes timeout
        response.raise_for_status()
        
        # Sauvegarder le fichier
        with open(csv_file, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Fichier CSV téléchargé : {csv_file}")
        
        # Charger le DataFrame
        df = pd.read_csv(csv_file, encoding='utf-8', sep=';')
        logger.info(f"Données chargées : {len(df)} enregistrements")
        
        return df
        
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement CSV : {e}")
        raise RuntimeError(f"Impossible de télécharger le fichier CSV : {e}")

def filter_department_06(df: pd.DataFrame) -> pd.DataFrame:
    """Filtre les données pour le département 06."""
    logger.info("Filtrage des données pour le département 06...")
    
    # Afficher les colonnes disponibles
    logger.info(f"Colonnes disponibles : {list(df.columns)}")
    
    # Filtrer par département
    if 'code_departement' in df.columns:
        df_06 = df[df['code_departement'] == '06'].copy()
    elif 'Code Département' in df.columns:
        df_06 = df[df['Code Département'] == '06'].copy()
    else:
        # Essayer de filtrer par code commune
        if 'code_commune' in df.columns:
            df_06 = df[df['code_commune'].str.startswith('06')].copy()
        elif 'Code Commune' in df.columns:
            df_06 = df[df['Code Commune'].str.startswith('06')].copy()
        else:
            logger.error("Impossible de filtrer par département - colonnes non trouvées")
            return pd.DataFrame()
    
    logger.info(f"Données département 06 : {len(df_06)} enregistrements")
    return df_06

def analyze_prospects(df: pd.DataFrame, seuil_mwh: float) -> Dict[str, Any]:
    """Analyse les prospects dans les données."""
    logger.info("Analyse des prospects...")
    
    if df.empty:
        logger.error("Aucune donnée à analyser")
        return {}
    
    # Identifier la colonne de consommation
    conso_cols = [col for col in df.columns if 'consommation' in col.lower() and 'mwh' in col.lower()]
    
    if not conso_cols:
        logger.error("Aucune colonne de consommation trouvée")
        logger.info(f"Colonnes disponibles : {list(df.columns)}")
        return {}
    
    conso_col = conso_cols[0]  # Prendre la première colonne de consommation
    logger.info(f"Utilisation de la colonne : {conso_col}")
    
    # Convertir en numérique si nécessaire
    df[conso_col] = pd.to_numeric(df[conso_col], errors='coerce')
    
    # Créer une colonne en kWh
    df['consommation_kwh'] = df[conso_col] * 1000
    
    # Filtrer les prospects (consommation > seuil)
    seuil_kwh = seuil_mwh * 1000
    prospects = df[df['consommation_kwh'] > seuil_kwh].copy()
    
    logger.info(f"Prospects identifiés (>{seuil_kwh:.0f} kWh) : {len(prospects)}")
    
    if len(prospects) == 0:
        logger.warning("Aucun prospect trouvé avec ce seuil")
        return {
            'nb_total': len(df),
            'nb_prospects': 0,
            'nb_communes': 0,
            'nb_iris': 0,
            'conso_moyenne': 0,
            'conso_totale': 0,
            'top_communes': [],
            'top_iris': []
        }
    
    # Identifier les colonnes pour l'analyse
    commune_cols = [col for col in df.columns if 'commune' in col.lower()]
    iris_cols = [col for col in df.columns if 'iris' in col.lower()]
    logement_cols = [col for col in df.columns if 'logement' in col.lower()]
    
    # Statistiques par commune
    stats_communes = pd.DataFrame()
    if commune_cols:
        code_commune_col = [col for col in commune_cols if 'code' in col.lower()]
        nom_commune_col = [col for col in commune_cols if 'nom' in col.lower()]
        
        if code_commune_col and nom_commune_col:
            group_cols = [code_commune_col[0], nom_commune_col[0]]
            
            agg_dict = {'consommation_kwh': ['count', 'sum', 'mean']}
            if logement_cols:
                agg_dict[logement_cols[0]] = 'sum'
            
            stats_communes = prospects.groupby(group_cols).agg(agg_dict).round(2)
            
            # Aplatir les colonnes
            new_cols = ['nb_prospects', 'conso_totale_kwh', 'conso_moyenne_kwh']
            if logement_cols:
                new_cols.append('total_logements')
            
            stats_communes.columns = new_cols
            stats_communes = stats_communes.reset_index()
            stats_communes = stats_communes.sort_values('nb_prospects', ascending=False)
    
    # Statistiques par IRIS
    stats_iris = pd.DataFrame()
    if iris_cols:
        code_iris_col = [col for col in iris_cols if 'code' in col.lower()]
        nom_iris_col = [col for col in iris_cols if 'nom' in col.lower()]
        
        if code_iris_col and nom_iris_col:
            group_cols = [code_iris_col[0], nom_iris_col[0]]
            
            agg_dict = {'consommation_kwh': ['count', 'sum', 'mean']}
            if logement_cols:
                agg_dict[logement_cols[0]] = 'sum'
            
            stats_iris = prospects.groupby(group_cols).agg(agg_dict).round(2)
            
            # Aplatir les colonnes
            new_cols = ['nb_prospects', 'conso_totale_kwh', 'conso_moyenne_kwh']
            if logement_cols:
                new_cols.append('total_logements')
            
            stats_iris.columns = new_cols
            stats_iris = stats_iris.reset_index()
            stats_iris = stats_iris.sort_values('nb_prospects', ascending=False)
    
    # Résumé des statistiques
    stats = {
        'nb_total': len(df),
        'nb_prospects': len(prospects),
        'nb_communes': len(stats_communes),
        'nb_iris': len(stats_iris),
        'conso_moyenne': prospects['consommation_kwh'].mean(),
        'conso_totale': prospects['consommation_kwh'].sum(),
        'top_communes': stats_communes.head(10).to_dict('records') if len(stats_communes) > 0 else [],
        'top_iris': stats_iris.head(10).to_dict('records') if len(stats_iris) > 0 else []
    }
    
    return stats, df, prospects, stats_communes, stats_iris

def save_results(data_dir: Path, df: pd.DataFrame, prospects: pd.DataFrame, 
                stats_communes: pd.DataFrame, stats_iris: pd.DataFrame):
    """Sauvegarde les résultats."""
    logger.info("Sauvegarde des résultats...")
    
    # Sauvegarder les données du département 06
    df.to_csv(data_dir / 'donnees_06.csv', index=False, encoding='utf-8')
    
    # Sauvegarder les prospects
    if len(prospects) > 0:
        prospects.to_csv(data_dir / 'prospects_06.csv', index=False, encoding='utf-8')
    
    # Sauvegarder les statistiques
    if len(stats_communes) > 0:
        stats_communes.to_csv(data_dir / 'stats_communes_06.csv', index=False, encoding='utf-8')
    
    if len(stats_iris) > 0:
        stats_iris.to_csv(data_dir / 'stats_iris_06.csv', index=False, encoding='utf-8')

def generate_report(data_dir: Path, stats: Dict[str, Any], seuil_mwh: float) -> Path:
    """Génère un rapport d'analyse."""
    report_path = data_dir / 'rapport_prospects_06.md'
    
    pourcentage = (stats['nb_prospects']/stats['nb_total']*100) if stats['nb_total'] > 0 else 0
    
    report_content = f"""# Rapport d'Analyse des Prospects Solaires - Département 06

## Informations générales
- **Date d'exécution** : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- **Département ciblé** : 06 (Alpes-Maritimes)
- **Seuil de consommation** : {seuil_mwh * 1000:.0f} kWh ({seuil_mwh} MWh)

## Statistiques globales
- **Total adresses analysées** : {stats['nb_total']:,}
- **Prospects identifiés** : {stats['nb_prospects']:,} ({pourcentage:.1f}%)
- **Communes avec prospects** : {stats['nb_communes']:,}
- **IRIS avec prospects** : {stats['nb_iris']:,}
- **Consommation moyenne des prospects** : {stats['conso_moyenne']:.0f} kWh
- **Consommation totale des prospects** : {stats['conso_totale']:.0f} kWh

## Top 10 des communes par nombre de prospects

| Rang | Commune | Prospects | Conso totale (kWh) | Conso moyenne (kWh) |
|------|---------|-----------|-------------------|-------------------|"""

    for i, commune in enumerate(stats['top_communes'], 1):
        commune_name = list(commune.values())[1] if len(commune.values()) > 1 else "N/A"
        nb_prospects = commune.get('nb_prospects', 0)
        conso_totale = commune.get('conso_totale_kwh', 0)
        conso_moyenne = commune.get('conso_moyenne_kwh', 0)
        report_content += f"\n| {i} | {commune_name} | {nb_prospects:.0f} | {conso_totale:.0f} | {conso_moyenne:.0f} |"

    if stats['top_iris']:
        report_content += f"""

## Top 10 des IRIS par nombre de prospects

| Rang | IRIS | Prospects | Conso totale (kWh) | Conso moyenne (kWh) |
|------|------|-----------|-------------------|-------------------|"""

        for i, iris in enumerate(stats['top_iris'], 1):
            iris_name = list(iris.values())[1] if len(iris.values()) > 1 else "N/A"
            nb_prospects = iris.get('nb_prospects', 0)
            conso_totale = iris.get('conso_totale_kwh', 0)
            conso_moyenne = iris.get('conso_moyenne_kwh', 0)
            report_content += f"\n| {i} | {iris_name} | {nb_prospects:.0f} | {conso_totale:.0f} | {conso_moyenne:.0f} |"

    report_content += f"""

## Fichiers générés
- `donnees_06.csv` : Toutes les données du département 06
- `prospects_06.csv` : Liste détaillée des prospects
- `stats_communes_06.csv` : Statistiques par commune
- `stats_iris_06.csv` : Statistiques par IRIS

## Sources des données
- **Données de consommation** : © Enedis – Open Licence 2.0
  - Seuil de confidentialité ≥10 logements
  - Export CSV : data.enedis.fr

---
*Généré automatiquement par OptimPV - {datetime.now().strftime('%Y')}*
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Rapport généré : {report_path}")
    return report_path

def main(seuil_mwh: float = CONFIG['SEUIL_CONSO_DEFAULT']):
    """Pipeline principal de traitement."""
    logger.info("=== DÉBUT DE L'ANALYSE PROSPECTS 06 ===")
    logger.info(f"Paramètres : seuil={seuil_mwh} MWh ({seuil_mwh*1000:.0f} kWh)")
    
    try:
        # Créer le répertoire de données
        data_dir = create_data_directory()
        
        # Téléchargement des données CSV
        logger.info("ÉTAPE 1 : Téléchargement du fichier CSV")
        df_complete = download_csv_data(data_dir)
        
        # Filtrage département 06
        logger.info("ÉTAPE 2 : Filtrage département 06")
        df_06 = filter_department_06(df_complete)
        
        if df_06.empty:
            raise RuntimeError("Aucune donnée trouvée pour le département 06")
        
        # Analyse des données
        logger.info("ÉTAPE 3 : Analyse des données")
        result = analyze_prospects(df_06, seuil_mwh)
        
        if not result:
            raise RuntimeError("Échec de l'analyse des données")
        
        stats, df_06, prospects, stats_communes, stats_iris = result
        
        # Sauvegarde des résultats
        logger.info("ÉTAPE 4 : Sauvegarde des résultats")
        save_results(data_dir, df_06, prospects, stats_communes, stats_iris)
        
        # Génération du rapport
        logger.info("ÉTAPE 5 : Génération du rapport")
        report_path = generate_report(data_dir, stats, seuil_mwh)
        
        # Résumé final
        logger.info("=== ANALYSE TERMINÉE AVEC SUCCÈS ===")
        logger.info(f"Prospects identifiés : {stats['nb_prospects']:,}")
        logger.info(f"Communes avec prospects : {stats['nb_communes']:,}")
        logger.info(f"Fichiers générés dans : {data_dir}")
        logger.info(f"Rapport : {report_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erreur fatale : {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse des prospects solaires - Département 06")
    parser.add_argument('--seuil', type=float, default=CONFIG['SEUIL_CONSO_DEFAULT'],
                       help=f"Seuil de consommation en MWh (défaut: {CONFIG['SEUIL_CONSO_DEFAULT']})")
    
    args = parser.parse_args()
    
    try:
        main(seuil_mwh=args.seuil)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Échec du traitement : {e}")
        sys.exit(1) 