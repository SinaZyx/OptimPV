# Fichier: modules/financial_summary_table.py

import streamlit as st
import pandas as pd
import numpy as np

def display_financial_summary_table(results: dict | None):
    """
    Affiche un tableau de synthèse financière et énergétique annuelle.

    Args:
        results: Le dictionnaire de résultats retourné par
                 analysis_engine.calculate_financial_indicators.
                 Peut être None si les résultats ne sont pas disponibles.
    """
    if results is None or not isinstance(results, dict):
        st.warning("Données de résultats non disponibles pour afficher le tableau financier.")
        return

    # Noms des lignes pour le tableau (ordre d'affichage)
    # AJOUT des lignes Production / Consommation / Surplus
    row_labels_ordered = [
        # Flux Énergétiques (kWh)
        "Production Annuelle (kWh)",
        "Consommation Annuelle (kWh)",
        "Autoconsommation Annuelle (kWh)", # AJOUTÉ pour info
        "Surplus Annuel (kWh)",
        # P&L (€)
        "Total Revenus",
        "OPEX Annuel Calculé",
        "EBITDA",
        "Amortissement",
        "EBIT",
        "Intérêts Payés",
        "EBT (Résultat Avant Impôts)",
        "Impôts Estimés",
        "Résultat Net",
        # Cash Flow (€)
        "(-) Investissement Net Fonds Propres (T0)", # Spécifique Année 0
        "(+) Amortissement", # Ligne pour la partie CF
        "(-) Remboursement Principal",
        "Free Cash Flow Equity (FCFE)",
        "Flux de Trésorerie Cumulé",
        # Indicateur Optionnel
        "DSCR Annuel"
    ]

    # Extraire les données nécessaires (avec gestion des erreurs si clé manque)
    try:
        years_list = results.get('years', [])
        if not years_list:
             st.error("Données d'années manquantes dans les résultats.")
             return
        num_years = len(years_list)
        # Créer les noms de colonnes pour Année 1 à N
        year_cols = [f"Année {y}" for y in years_list]

        # Créer un dictionnaire pour construire le DataFrame
        # AJOUT des données énergétiques
        data_for_df = {
            "Production Annuelle (kWh)": results.get('annual_production', np.zeros(num_years)),
            "Consommation Annuelle (kWh)": results.get('annual_consumption', np.zeros(num_years)),
            "Autoconsommation Annuelle (kWh)": results.get('annual_autoconsumption', np.zeros(num_years)), # AJOUTÉ
            "Surplus Annuel (kWh)": results.get('annual_surplus', np.zeros(num_years)),
            # Données financières (inchangées)
            "Total Revenus": results.get('revenues', np.zeros(num_years)),
            "OPEX Annuel Calculé": results.get('opex', np.zeros(num_years)),
            "EBITDA": results.get('ebitda', np.zeros(num_years)),
            "Amortissement": results.get('depreciation', np.zeros(num_years)),
            "EBIT": results.get('ebit', np.zeros(num_years)),
            "Intérêts Payés": results.get('interest_paid', np.zeros(num_years)),
            "EBT (Résultat Avant Impôts)": results.get('ebt', np.zeros(num_years)),
            "Impôts Estimés": results.get('taxes', np.zeros(num_years)),
            "Résultat Net": results.get('net_income', np.zeros(num_years)),
            "(+) Amortissement": results.get('depreciation', np.zeros(num_years)),
            "(-) Remboursement Principal": -np.array(results.get('principal_paid', np.zeros(num_years))),
            "Free Cash Flow Equity (FCFE)": results.get('free_cash_flow', np.zeros(num_years)),
            "DSCR Annuel": results.get('dscr', np.full(num_years, np.nan))
        }

        # Gérer l'investissement initial et le flux cumulé (inchangé)
        initial_investment = results.get('net_equity_investment', 0)
        cumulative_flow_data = results.get('cumulative_cash_flow', np.zeros(num_years))

        # Créer le DataFrame avec les années comme index initialement
        df = pd.DataFrame(data_for_df, index=years_list)

        # Ajouter la ligne pour l'année 0 et le flux cumulé (inchangé)
        df.loc[0] = 0
        df = df.sort_index()
        df.loc[0, "(-) Investissement Net Fonds Propres (T0)"] = -initial_investment
        cumulative_flow_with_t0 = np.concatenate(([-initial_investment], cumulative_flow_data))
        df["Flux de Trésorerie Cumulé"] = cumulative_flow_with_t0

        # Mettre les années en colonnes et les items en index (inchangé)
        df = df.T
        df = df.rename(columns={y: f"Année {y}" for y in years_list}, index={0: 'Année 0'})

        # S'assurer que les lignes spécifiques T0 et Cumulé existent (inchangé)
        if "(-) Investissement Net Fonds Propres (T0)" not in df.index:
             df.loc["(-) Investissement Net Fonds Propres (T0)"] = 0
             df.loc["(-) Investissement Net Fonds Propres (T0)", "Année 0"] = -initial_investment
        if "Flux de Trésorerie Cumulé" not in df.index:
             df.loc["Flux de Trésorerie Cumulé"] = 0
             df.loc["Flux de Trésorerie Cumulé", "Année 0"] = -initial_investment
             df.loc["Flux de Trésorerie Cumulé", [f"Année {y}" for y in years_list]] = cumulative_flow_data

        # Réorganiser les lignes selon le nouvel ordre défini
        existing_labels = [label for label in row_labels_ordered if label in df.index]
        df = df.reindex(existing_labels)

        # Remplacer les NaN (inchangé pour l'instant, le formatage s'en chargera)
        df_display = df # On peut formater directement df

        # Définir les lignes qui doivent avoir le format kWh
        kwh_rows = [
            "Production Annuelle (kWh)",
            "Consommation Annuelle (kWh)",
            "Autoconsommation Annuelle (kWh)",
            "Surplus Annuel (kWh)"
        ]
        # Définir les lignes qui doivent avoir le format €
        euro_rows = df_display.index.difference(kwh_rows + ["DSCR Annuel"]).tolist() # Toutes les autres sauf DSCR

        # Formatage pour l'affichage (plus spécifique)
        styled_df = df_display.style.format(
             # Format kWh
             lambda x: f"{x:,.0f} kWh" if pd.notna(x) and isinstance(x, (int, float, np.number)) else ("N/A" if pd.isna(x) else x),
             subset=pd.IndexSlice[kwh_rows, :]
        ).format(
             # Format €
             lambda x: f"€ {x:,.0f}" if pd.notna(x) and isinstance(x, (int, float, np.number)) else ("N/A" if pd.isna(x) else x),
             subset=pd.IndexSlice[euro_rows, :]
        ).format(
             # Format DSCR
             lambda x: f"{x:.2f}" if pd.notna(x) and isinstance(x, (int, float, np.number)) else "N/A",
             subset=pd.IndexSlice[["DSCR Annuel"] if "DSCR Annuel" in df_display.index else [], :]
        )

        # Afficher le DataFrame stylisé
        st.dataframe(styled_df, use_container_width=True)

    except KeyError as e:
        st.error(f"Erreur: Clé manquante dans les résultats pour le tableau financier : {e}")
        st.write("Résultats reçus:", results)
    except Exception as e:
        st.error(f"Erreur inattendue lors de la création du tableau financier : {e}")
        import traceback
        st.error(traceback.format_exc())

# --- Fin du fichier modules/financial_summary_table.py ---