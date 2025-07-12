# modules/tax_engine.py
import numpy as np

# --- Constantes Fiscales (ajustables si nécessaire) ---
LOSS_CARRYFORWARD_CAP_BASE = 1_000_000.0 # Plafond de base pour imputation déficit
LOSS_CARRYFORWARD_CAP_PERCENT = 0.50    # Pourcentage applicable au-delà du plafond
PME_REDUCED_RATE_THRESHOLD = 42_500.0   # Seuil pour le taux réduit PME
PME_REDUCED_RATE = 0.15                 # Taux réduit IS PME
STANDARD_TAX_RATE = 0.25                # Taux normal IS (à synchroniser avec config si besoin)
ACOMPTE_COUNT = 4.0                     # Nombre d'acomptes IS par an

def apply_loss_carryforward_cap(ebt_before_loss: float, loss_carryforward_balance: float) -> tuple[float, float]:
    """
    Calcule le montant du déficit reportable utilisable cette année, en respectant le plafond légal,
    et retourne le bénéfice imposable après imputation et le nouveau solde de déficit reportable.

    Args:
        ebt_before_loss: Résultat avant impôts et avant imputation des déficits.
        loss_carryforward_balance: Solde des déficits reportables des années précédentes.

    Returns:
        Tuple[float, float]: (bénéfice_imposable_final, nouveau_solde_déficit_reportable)
    """
    if ebt_before_loss <= 0:
        # Si EBT négatif ou nul, on n'utilise pas de déficit, on l'accumule
        new_loss_balance = loss_carryforward_balance + abs(ebt_before_loss)
        taxable_ebt = 0.0 # Pas de bénéfice imposable
        loss_used_this_year = 0.0
    else:
        # Calcul du plafond d'imputation
        max_loss_offset_allowed = LOSS_CARRYFORWARD_CAP_BASE + max(0, ebt_before_loss - LOSS_CARRYFORWARD_CAP_BASE) * LOSS_CARRYFORWARD_CAP_PERCENT

        # Montant du déficit utilisable cette année
        loss_to_use = min(loss_carryforward_balance, ebt_before_loss, max_loss_offset_allowed)
        loss_used_this_year = loss_to_use if loss_to_use > 1e-9 else 0.0 # Eviter -0.0

        # Calcul du bénéfice imposable
        taxable_ebt = ebt_before_loss - loss_used_this_year

        # Mise à jour du solde de déficit reportable
        new_loss_balance = loss_carryforward_balance - loss_used_this_year

    # S'assurer qu'on ne renvoie pas de valeurs négatives très petites
    taxable_ebt = max(0.0, taxable_ebt)
    new_loss_balance = max(0.0, new_loss_balance)

    #print(f"DEBUG TAX: EBT={ebt_before_loss:.0f}, LossIn={loss_carryforward_balance:.0f}, MaxUse={max_loss_offset_allowed:.0f}, Used={loss_used_this_year:.0f}, Taxable={taxable_ebt:.0f}, LossOut={new_loss_balance:.0f}")

    return taxable_ebt, new_loss_balance


def calculate_corporate_tax_pme(taxable_ebt: float) -> float:
    """
    Calcule l'impôt sur les sociétés en appliquant le double taux PME (15%/25%).

    Args:
        taxable_ebt: Bénéfice imposable (après imputation des déficits).

    Returns:
        float: Montant total de l'IS dû pour l'année.
    """
    if taxable_ebt <= 0:
        return 0.0

    # Part taxable au taux réduit
    taxable_at_reduced_rate = min(taxable_ebt, PME_REDUCED_RATE_THRESHOLD)
    tax_reduced_part = taxable_at_reduced_rate * PME_REDUCED_RATE

    # Part taxable au taux normal
    taxable_at_standard_rate = max(0, taxable_ebt - PME_REDUCED_RATE_THRESHOLD)
    tax_standard_part = taxable_at_standard_rate * STANDARD_TAX_RATE

    total_tax = tax_reduced_part + tax_standard_part
    return max(0.0, total_tax) # Assurer non-négatif


def calculate_quarterly_installment(previous_year_tax: float) -> float:
    """
    Calcule le montant d'un acompte trimestriel basé sur l'IS de l'année précédente.

    Args:
        previous_year_tax: IS total calculé pour l'exercice N-1.

    Returns:
        float: Montant d'un acompte trimestriel pour l'année N.
    """
    if previous_year_tax < 3000: # Seuil d'exonération des acomptes
        return 0.0
    else:
        # Pourrait être plus complexe (ex: basé sur IS N-2 pour 1er acompte),
        # mais on simplifie ici : 1/4 de l'IS N-1.
        return max(0.0, previous_year_tax / ACOMPTE_COUNT)