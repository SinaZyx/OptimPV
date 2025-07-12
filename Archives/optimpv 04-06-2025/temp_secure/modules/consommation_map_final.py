#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse des prospects solaires - Département 06 (Version finale)

CONTEXTE : Prospection solaire / autoconsommation collective
Objectif : Analyser les prospects basés sur les données Enedis disponibles

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
        'ADRESSE_API': 'https://data.enedis.fr/api/explore/v2.1/catalog/datasets/consommation-annuelle-residentielle-par-adresse/records'
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

def download_data_simple() -> pd.DataFrame:
    """Télécharge les données du département 06 de manière simple."""
    logger.info("Téléchargement des données Enedis pour le département 06...")
    
    url = CONFIG['URLS']['ADRESSE_API']
    all_data = []
    offset = 0
    limit = 10000
    
    while True:
        logger.info(f"Téléchargement batch offset={offset}")
        
        # Paramètres simples sans filtre complexe
        params = {
            'limit': limit,
            'offset': offset
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                break
            
            # Filtrer localement pour le département 06
            dept_06_results = [r for r in results if r.get('code_departement') == '06']
            
            if dept_06_results:
                all_data.extend(dept_06_results)
                logger.info(f"Trouvé {len(dept_06_results)} enregistrements pour le 06")
            
            # Si on a moins de résultats que demandé, on a atteint la fin
            if len(results) < limit:
                break
                
            offset += limit
            
            # Limite de sécurité pour éviter de télécharger trop
            if offset > 100000:
                logger.warning("Limite de téléchargement atteinte")
                break
                
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement : {e}")
            break
    
    if not all_data:
        raise RuntimeError("Aucune donnée trouvée pour le département 06")
    
    df = pd.json_normalize(all_data)
    logger.info(f"Total des données récupérées : {len(df)} enregistrements")
    
    return df

def analyze_prospects(df: pd.DataFrame, seuil_mwh: float) -> Dict[str, Any]:
    """Analyse les prospects dans les données."""
    logger.info("Analyse des prospects...")
    
    # Afficher les colonnes disponibles
    logger.info(f"Colonnes disponibles : {list(df.columns)}")
    
    # Convertir la consommation en kWh
    if 'consommation_annuelle_totale_de_l_adresse_mwh' in df.columns:
        df['consommation_kwh'] = df['consommation_annuelle_totale_de_l_adresse_mwh'] * 1000
        conso_col = 'consommation_kwh'
    else:
        logger.error("Colonne de consommation non trouvée")
        return {}
    
    # Filtrer les prospects (consommation > seuil)
    seuil_kwh = seuil_mwh * 1000
    prospects = df[df[conso_col] > seuil_kwh].copy()
    
    logger.info(f"Prospects identifiés (>{seuil_kwh:.0f} kWh) : {len(prospects)}")
    
    # Statistiques par commune
    if len(prospects) > 0:
        stats_communes = prospects.groupby(['code_commune', 'nom_commune']).agg({
            conso_col: ['count', 'sum', 'mean'],
            'nombre_de_logements': 'sum'
        }).round(2)
        
        stats_communes.columns = ['nb_prospects', 'conso_totale_kwh', 'conso_moyenne_kwh', 'total_logements']
        stats_communes = stats_communes.reset_index()
        stats_communes = stats_communes.sort_values('nb_prospects', ascending=False)
        
        # Top 10 des communes
        top_communes = stats_communes.head(10).to_dict('records')
    else:
        stats_communes = pd.DataFrame()
        top_communes = []
    
    # Statistiques par IRIS
    if len(prospects) > 0 and 'code_iris' in prospects.columns:
        stats_iris = prospects.groupby(['code_iris', 'nom_iris']).agg({
            conso_col: ['count', 'sum', 'mean'],
            'nombre_de_logements': 'sum'
        }).round(2)
        
        stats_iris.columns = ['nb_prospects', 'conso_totale_kwh', 'conso_moyenne_kwh', 'total_logements']
        stats_iris = stats_iris.reset_index()
        stats_iris = stats_iris.sort_values('nb_prospects', ascending=False)
        
        top_iris = stats_iris.head(10).to_dict('records')
    else:
        stats_iris = pd.DataFrame()
        top_iris = []
    
    # Résumé des statistiques
    stats = {
        'nb_total': len(df),
        'nb_prospects': len(prospects),
        'nb_communes': len(stats_communes),
        'nb_iris': len(stats_iris),
        'conso_moyenne': prospects[conso_col].mean() if len(prospects) > 0 else 0,
        'conso_totale': prospects[conso_col].sum() if len(prospects) > 0 else 0,
        'top_communes': top_communes,
        'top_iris': top_iris
    }
    
    return stats, df, prospects, stats_communes, stats_iris

def save_results(data_dir: Path, df: pd.DataFrame, prospects: pd.DataFrame, 
                stats_communes: pd.DataFrame, stats_iris: pd.DataFrame):
    """Sauvegarde les résultats."""
    logger.info("Sauvegarde des résultats...")
    
    # Sauvegarder les données brutes
    df.to_csv(data_dir / 'donnees_brutes_06.csv', index=False, encoding='utf-8')
    
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
    
    report_content = f"""# Rapport d'Analyse des Prospects Solaires - Département 06

## Informations générales
- **Date d'exécution** : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
- **Département ciblé** : 06 (Alpes-Maritimes)
- **Seuil de consommation** : {seuil_mwh * 1000:.0f} kWh ({seuil_mwh} MWh)

## Statistiques globales
- **Total adresses analysées** : {stats['nb_total']:,}
- **Prospects identifiés** : {stats['nb_prospects']:,} ({stats['nb_prospects']/stats['nb_total']*100:.1f}% si > 0 sinon 0)
- **Communes avec prospects** : {stats['nb_communes']:,}
- **IRIS avec prospects** : {stats['nb_iris']:,}
- **Consommation moyenne des prospects** : {stats['conso_moyenne']:.0f} kWh
- **Consommation totale des prospects** : {stats['conso_totale']:.0f} kWh

## Top 10 des communes par nombre de prospects

| Rang | Code | Commune | Prospects | Conso totale (kWh) | Conso moyenne (kWh) | Logements |
|------|------|---------|-----------|-------------------|-------------------|-----------|"""

    for i, commune in enumerate(stats['top_communes'], 1):
        report_content += f"\n| {i} | {commune['code_commune']} | {commune['nom_commune']} | {commune['nb_prospects']:.0f} | {commune['conso_totale_kwh']:.0f} | {commune['conso_moyenne_kwh']:.0f} | {commune['total_logements']:.0f} |"

    if stats['top_iris']:
        report_content += f"""

## Top 10 des IRIS par nombre de prospects

| Rang | Code IRIS | Nom IRIS | Prospects | Conso totale (kWh) | Conso moyenne (kWh) | Logements |
|------|-----------|----------|-----------|-------------------|-------------------|-----------|"""

        for i, iris in enumerate(stats['top_iris'], 1):
            report_content += f"\n| {i} | {iris['code_iris']} | {iris['nom_iris']} | {iris['nb_prospects']:.0f} | {iris['conso_totale_kwh']:.0f} | {iris['conso_moyenne_kwh']:.0f} | {iris['total_logements']:.0f} |"

    report_content += f"""

## Fichiers générés
- `donnees_brutes_06.csv` : Toutes les données du département 06
- `prospects_06.csv` : Liste détaillée des prospects
- `stats_communes_06.csv` : Statistiques par commune
- `stats_iris_06.csv` : Statistiques par IRIS

## Sources des données
- **Données de consommation** : © Enedis – Open Licence 2.0
  - Seuil de confidentialité ≥10 logements
  - API : data.enedis.fr

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
        
        # Téléchargement des données
        logger.info("ÉTAPE 1 : Téléchargement des données")
        df = download_data_simple()
        
        # Analyse des données
        logger.info("ÉTAPE 2 : Analyse des données")
        result = analyze_prospects(df, seuil_mwh)
        
        if not result:
            raise RuntimeError("Échec de l'analyse des données")
        
        stats, df, prospects, stats_communes, stats_iris = result
        
        # Sauvegarde des résultats
        logger.info("ÉTAPE 3 : Sauvegarde des résultats")
        save_results(data_dir, df, prospects, stats_communes, stats_iris)
        
        # Génération du rapport
        logger.info("ÉTAPE 4 : Génération du rapport")
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