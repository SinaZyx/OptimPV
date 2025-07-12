# modules/engine_module/treasury_validator.py

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TreasuryValidator:
    """
    Validateur professionnel pour la cohérence des calculs de trésorerie et placements
    """
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_treasury_coherence(self, monthly_df: pd.DataFrame) -> dict:
        """
        Valide la cohérence de la trésorerie et des placements
        
        Returns:
            dict: Résultat de validation avec erreurs et avertissements
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # 1. Vérifier que la trésorerie varie
        self._check_treasury_variation(monthly_df)
        
        # 2. Vérifier la cohérence placements vs trésorerie
        self._check_placement_coherence(monthly_df)
        
        # 3. Vérifier les ratios de sécurité
        self._check_security_ratios(monthly_df)
        
        # 4. Vérifier l'évolution des intérêts
        self._check_interest_progression(monthly_df)
        
        return {
            'is_valid': len(self.validation_errors) == 0,
            'errors': self.validation_errors,
            'warnings': self.validation_warnings,
            'summary': self._generate_summary(monthly_df)
        }
    
    def _check_treasury_variation(self, monthly_df: pd.DataFrame):
        """Vérifie que la trésorerie varie et n'est pas constante"""
        if 'Solde_Tresorerie_Fin_Mois' in monthly_df.columns:
            treasury_values = monthly_df['Solde_Tresorerie_Fin_Mois'].dropna()
            
            if len(treasury_values) > 1:
                # Vérifier si la trésorerie varie
                min_val = treasury_values.min()
                max_val = treasury_values.max()
                variation = max_val - min_val
                
                if variation < 1.0:  # Moins de 1€ de variation
                    self.validation_errors.append(
                        f"TRÉSORERIE CONSTANTE: La trésorerie reste fixe à {min_val:,.0f}€. "
                        f"Vérifier que les flux (FCFE) sont correctement calculés."
                    )
                elif variation < 100.0:  # Moins de 100€ de variation
                    self.validation_warnings.append(
                        f"FAIBLE VARIATION: La trésorerie varie peu ({variation:.0f}€). "
                        f"Vérifier que les flux sont significatifs."
                    )
                else:
                    logger.info(f"✅ Trésorerie varie correctement: {min_val:,.0f}€ à {max_val:,.0f}€")
    
    def _check_placement_coherence(self, monthly_df: pd.DataFrame):
        """Vérifie la cohérence entre placements et trésorerie"""
        required_cols = [
            'Solde_Tresorerie_Fin_Mois', 
            'Total_Placements_TVA', 
            'Fonds_Reserve_Onduleur_Total'
        ]
        
        if all(col in monthly_df.columns for col in required_cols):
            for idx, row in monthly_df.iterrows():
                treasury = row.get('Solde_Tresorerie_Fin_Mois', 0)
                tva_placements = row.get('Total_Placements_TVA', 0)
                reserve_fund = row.get('Fonds_Reserve_Onduleur_Total', 0)
                excedent_placements = row.get('Solde_Placement_Excedents_Cumul', 0)
                
                total_placements = tva_placements + excedent_placements
                
                # Le fonds de réserve est séparé comptablement mais doit être cohérent
                if total_placements > treasury + 1000:  # Tolérance de 1000€
                    self.validation_errors.append(
                        f"INCOHÉRENCE MOIS {idx.strftime('%Y-%m')}: "
                        f"Placements ({total_placements:,.0f}€) > Trésorerie ({treasury:,.0f}€). "
                        f"Impossible de placer plus que disponible."
                    )
                
                # Vérifier que les ratios sont cohérents
                if treasury > 0 and total_placements > treasury * 0.95:
                    self.validation_warnings.append(
                        f"PLACEMENT ÉLEVÉ MOIS {idx.strftime('%Y-%m')}: "
                        f"95%+ de la trésorerie est placée. Risque de liquidité."
                    )
    
    def _check_security_ratios(self, monthly_df: pd.DataFrame):
        """Vérifie les ratios de sécurité"""
        if 'Reserve_Minimum_Requise' in monthly_df.columns and 'Solde_Tresorerie_Fin_Mois' in monthly_df.columns:
            for idx, row in monthly_df.iterrows():
                treasury = row.get('Solde_Tresorerie_Fin_Mois', 0)
                min_reserve = row.get('Reserve_Minimum_Requise', 0)
                
                if min_reserve > 0:
                    ratio = treasury / min_reserve
                    
                    if ratio < 0.5:
                        self.validation_errors.append(
                            f"RATIO CRITIQUE MOIS {idx.strftime('%Y-%m')}: "
                            f"Trésorerie ({treasury:,.0f}€) < 50% réserve minimum ({min_reserve:,.0f}€). "
                            f"Ratio: {ratio:.2f}x"
                        )
                    elif ratio < 1.0:
                        self.validation_warnings.append(
                            f"RATIO FAIBLE MOIS {idx.strftime('%Y-%m')}: "
                            f"Trésorerie ({treasury:,.0f}€) < réserve minimum ({min_reserve:,.0f}€). "
                            f"Ratio: {ratio:.2f}x"
                        )
    
    def _check_interest_progression(self, monthly_df: pd.DataFrame):
        """Vérifie la progression logique des intérêts"""
        if 'Interets_Totaux_Mensuels' in monthly_df.columns:
            interest_values = monthly_df['Interets_Totaux_Mensuels'].fillna(0)
            
            # Vérifier qu'il y a des intérêts si des placements existent
            if 'Total_Placements_TVA' in monthly_df.columns:
                placement_values = monthly_df['Total_Placements_TVA'].fillna(0)
                
                # Si des placements existent mais pas d'intérêts
                months_with_placements = (placement_values > 1000).sum()
                months_with_interests = (interest_values > 0.01).sum()
                
                if months_with_placements > 6 and months_with_interests == 0:
                    self.validation_errors.append(
                        f"INTÉRÊTS MANQUANTS: {months_with_placements} mois avec placements "
                        f"mais aucun intérêt généré. Vérifier les taux."
                    )
                elif months_with_placements > months_with_interests + 3:
                    self.validation_warnings.append(
                        f"INTÉRÊTS PARTIELS: {months_with_placements} mois avec placements "
                        f"mais seulement {months_with_interests} mois avec intérêts."
                    )
    
    def _generate_summary(self, monthly_df: pd.DataFrame) -> dict:
        """Génère un résumé de l'état de la trésorerie"""
        summary = {}
        
        if 'Solde_Tresorerie_Fin_Mois' in monthly_df.columns:
            treasury = monthly_df['Solde_Tresorerie_Fin_Mois']
            summary['treasury'] = {
                'initial': float(treasury.iloc[0]) if len(treasury) > 0 else 0,
                'final': float(treasury.iloc[-1]) if len(treasury) > 0 else 0,
                'min': float(treasury.min()),
                'max': float(treasury.max()),
                'variation': float(treasury.max() - treasury.min())
            }
        
        if 'Total_Placements_TVA' in monthly_df.columns:
            placements = monthly_df['Total_Placements_TVA'].fillna(0)
            summary['placements'] = {
                'final': float(placements.iloc[-1]) if len(placements) > 0 else 0,
                'max': float(placements.max())
            }
        
        if 'Interets_Totaux_Mensuels' in monthly_df.columns:
            interests = monthly_df['Interets_Totaux_Mensuels'].fillna(0)
            summary['interests'] = {
                'total': float(interests.sum()),
                'monthly_avg': float(interests.mean()),
                'months_with_interests': int((interests > 0.01).sum())
            }
        
        return summary

def validate_treasury_data(monthly_df: pd.DataFrame) -> dict:
    """
    Fonction utilitaire pour valider les données de trésorerie
    
    Args:
        monthly_df: DataFrame avec les données mensuelles
        
    Returns:
        dict: Résultat de validation
    """
    validator = TreasuryValidator()
    return validator.validate_treasury_coherence(monthly_df)