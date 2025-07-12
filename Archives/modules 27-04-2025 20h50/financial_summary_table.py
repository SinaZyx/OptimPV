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
    # --- AJOUT PRINT DEBUG ---
    print(f"DEBUG TABLE: results reçu (extrait clés) = {list(results.keys()) if results else 'None'}")
    print(f"DEBUG TABLE: results['turpe'] reçu = {results.get('turpe', 'NON TROUVÉ')[:5]}...")
    # --- FIN AJOUT ---

    if results is None or not isinstance(results, dict):
        st.warning("Données de résultats non disponibles pour afficher le tableau financier.")
        return

    # Noms des lignes pour le tableau (ordre d'affichage mis à jour)
    row_labels_ordered = [
        # Flux Énergétiques (kWh)
        "Production Annuelle (kWh)",
        "Consommation Annuelle (kWh)",
        "Autoconsommation Annuelle (kWh)",
        "Surplus Annuel (kWh)",
        # P&L (€)
        "Total Revenus",
        "OPEX Annuel Calculé",
        "TURPE Annuelle",
        "EBITDA",
        "Amortissement",
        "EBIT",
        "Intérêts Payés",
        "EBT (Résultat Avant Impôts)",
        "Impôts Estimés",
        "Résultat Net",
        # Cash Flow Projet (€) - Section Optionnelle Ajoutée
        "Operating Cash Flow Projet",
        # Cash Flow Equity (€)
        "(-) Investissement Net Fonds Propres (T0)",
        "(+) Amortissement",
        "Service de la Dette Annuel",
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
        year_cols = [f"Année {y}" for y in years_list]

        # Créer un dictionnaire pour construire le DataFrame (ajouter les nouvelles clés)
        data_for_df = {
            # Énergie (kWh)
            "Production Annuelle (kWh)": results.get('annual_production', np.zeros(num_years)),
            "Consommation Annuelle (kWh)": results.get('annual_consumption', np.zeros(num_years)),
            "Autoconsommation Annuelle (kWh)": results.get('annual_autoconsumption', np.zeros(num_years)),
            "Surplus Annuel (kWh)": results.get('annual_surplus', np.zeros(num_years)),
            # P&L (€)
            "Total Revenus": results.get('revenues', np.zeros(num_years)),
            "OPEX Annuel Calculé": results.get('opex', np.zeros(num_years)),
            "TURPE Annuelle": results.get('turpe', np.zeros(num_years)),
            "EBITDA": results.get('ebitda', np.zeros(num_years)),
            "Amortissement": results.get('depreciation', np.zeros(num_years)),
            "EBIT": results.get('ebit', np.zeros(num_years)),
            "Intérêts Payés": results.get('interest_paid', np.zeros(num_years)),
            "EBT (Résultat Avant Impôts)": results.get('ebt', np.zeros(num_years)),
            "Impôts Estimés": results.get('taxes', np.zeros(num_years)),
            "Résultat Net": results.get('net_income', np.zeros(num_years)),
            # Cash Flow Projet (€)
            "Operating Cash Flow Projet": results.get('operating_cash_flow', np.zeros(num_years)),
            # Cash Flow Equity (€) - Composants et résultat
            "(+) Amortissement": results.get('depreciation', np.zeros(num_years)),
            "Service de la Dette Annuel": results.get('debt_service', np.zeros(num_years)),
            "(-) Remboursement Principal": -np.array(results.get('principal_paid', np.zeros(num_years))),
            "Free Cash Flow Equity (FCFE)": results.get('free_cash_flow', np.zeros(num_years)),
            # Indicateurs & Cumul
            "DSCR Annuel": results.get('dscr', np.full(num_years, np.nan))
        }

        # Gérer l'investissement initial et le flux cumulé (inchangé)
        initial_investment = results.get('net_equity_investment', 0)
        cumulative_flow_data = results.get('cumulative_cash_flow', np.zeros(num_years))

        # Créer le DataFrame
        df = pd.DataFrame(data_for_df, index=years_list)
        
        # Ajouter et trier l'année 0
        df.loc[0] = 0 
        df = df.sort_index()

        # Ligne spécifique pour l'investissement T0
        df.loc[0, "(+) Amortissement"] = 0
        df.loc[0, "(-) Remboursement Principal"] = 0
        df.loc[0, "Service de la Dette Annuel"] = 0
        df.loc[0, "Free Cash Flow Equity (FCFE)"] = -initial_investment
        if "(-) Investissement Net Fonds Propres (T0)" not in df.columns:
             df["(-) Investissement Net Fonds Propres (T0)"] = 0.0
        df.loc[0, "(-) Investissement Net Fonds Propres (T0)"] = -initial_investment
        
        # Ligne spécifique pour le flux cumulé (incluant T0)
        cumulative_flow_with_t0 = np.cumsum(np.concatenate(([df.loc[0, "Free Cash Flow Equity (FCFE)"]], df.loc[years_list, "Free Cash Flow Equity (FCFE)"].values)))
        if "Flux de Trésorerie Cumulé" not in df.columns:
             df["Flux de Trésorerie Cumulé"] = 0.0
        df["Flux de Trésorerie Cumulé"] = cumulative_flow_with_t0

        # Mettre les années en colonnes et les items en index (inchangé)
        df = df.T
        df = df.rename(columns={y: f"Année {y}" for y in years_list})
        df = df.rename(columns={0: 'Année 0'})

        # Réorganiser les lignes selon le nouvel ordre défini (incluant les nouvelles lignes)
        existing_labels = [label for label in row_labels_ordered if label in df.index]
        df = df.reindex(existing_labels)

        # Remplacer les NaN potentiels avant formatage (peut aider)
        df_display = df.fillna('N/A')

        # Mettre à jour la liste des lignes formatées en kWh et €
        kwh_rows = [
            "Production Annuelle (kWh)",
            "Consommation Annuelle (kWh)",
            "Autoconsommation Annuelle (kWh)",
            "Surplus Annuel (kWh)"
        ]
        euro_rows = df_display.index.difference(kwh_rows + ["DSCR Annuel"]).tolist()

        # Formatage pour l'affichage (devrait gérer les nouvelles lignes)
        def format_kwh(x):
            if isinstance(x, (int, float, np.number)): return f"{x:,.0f} kWh"
            return x
        def format_euro(x):
            if isinstance(x, (int, float, np.number)): return f"€ {x:,.0f}"
            return x
        def format_dscr(x):
            if isinstance(x, (int, float, np.number)): return f"{x:.2f}"
            return x

        styled_df = df_display.style
        if kwh_rows:
            styled_df = styled_df.format(format_kwh, subset=pd.IndexSlice[[label for label in kwh_rows if label in df_display.index], :])
        if euro_rows:
            styled_df = styled_df.format(format_euro, subset=pd.IndexSlice[[label for label in euro_rows if label in df_display.index], :])
        if "DSCR Annuel" in df_display.index:
            styled_df = styled_df.format(format_dscr, subset=pd.IndexSlice["DSCR Annuel", :])

        st.dataframe(styled_df, use_container_width=True)

    except KeyError as e:
        st.error(f"Erreur: Clé manquante dans les résultats pour le tableau financier : {e}")
        if results: st.write("Clés disponibles dans les résultats:", list(results.keys()))
    except Exception as e:
        st.error(f"Erreur inattendue lors de la création du tableau financier : {e}")
        import traceback
        st.error(traceback.format_exc())

# --- Fin du fichier modules/financial_summary_table.py ---