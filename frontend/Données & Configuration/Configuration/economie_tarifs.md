# Configuration Économie & Tarifs - OptimPV

## Vue d'ensemble

L'onglet "Économie & Tarifs" de OptimPV permet de configurer tous les paramètres économiques et tarifaires du projet photovoltaïque selon l'implémentation réelle Streamlit. Cette section configure les paramètres macro-économiques, les tarifs d'obligation d'achat (OA), la valorisation de l'autoconsommation, les paramètres TURPE et les barèmes de subvention.

## Structure réelle de l'interface

### 1. Paramètres Macro-économiques

```typescript
interface MacroEconomicParameters {
 title: "Paramètres Macro-économiques & Tarifs";

 parameters: {
 taux_inflation: {
 label: "Taux d'inflation Général (%)";
 type: "number_input";
 min_value: 0.0;
 max_value: 10.0;
 value: number; // default: 2.0
 step: 0.1;
 help: "Inflation annuelle pour OPEX, TURPE (si indexé), prix EDF, etc.";
 };

 taux_imposition: {
 label: "Taux d'imposition Standard (%)";
 type: "number_input";
 min_value: 0.0;
 max_value: 50.0;
 value: number; // default: 25.0
 step: 0.1;
 help: "Taux standard (normalement 25%) appliqué sur la part du bénéfice imposable annuel excédant 42 500€. Le taux réduit PME (15% sur les premiers 42 500€) est appliqué automatiquement par le moteur de calcul.";
 };

 tarif_edf_reference: {
 label: "Tarif EDF de référence (€/kWh)";
 type: "number_input";
 min_value: 0.05;
 max_value: 0.50;
 value: number; // default: 0.21
 step: 0.01;
 format: "%.4f";
 help: "Tarif de comparaison pour le gain client";
 };
 };
}
```

### 2. Tarif d'Achat Surplus (OA)

```typescript
interface TariffOAConfiguration {
 title: "Tarif d'Achat Surplus (OA)";

 calculation: {
 tarif_oa_calculé: {
 type: "metric";
 label: "Tarif OA Applicable (calculé)";
 value: string; // Format: "X.XXXX €/kWh"
 help: string; // "Basé sur P_totale=XX.X kWc et barèmes ci-dessous"

 calculation_logic: {
 total_power: number; // sum of all sites power
 applied_rate: number; // from brackets below
 formula: "default_tarif_oa(total_power)"
 };
 };

 indexation: {
 tarif_oa_indexe_inflation: {
 type: "checkbox";
 label: "Indexer le Tarif OA sur Inflation Spécifique?";
 value: boolean; // default: true
 };

 taux_inflation_tarif_oa: {
 type: "number_input";
 label: "-> Taux Inflation OA (%)";
 min_value: 0.0;
 max_value: 10.0;
 value: number; // default: 1.89
 step: 0.1;
 visible: boolean; // only if indexation enabled
 };
 };
 };

 brackets: {
 expander_title: " Configuration Barèmes Tarif OA";

 rates: {
 tarif_oa_bracket_le9: {
 label: "Barème si P <= 9 kWc (€/kWh)";
 type: "number_input";
 min_value: 0.0;
 value: number; // default: 0.0400
 step: 0.0001;
 format: "%.4f";
 };

 tarif_oa_bracket_le100: {
 label: "Barème si 9 < P <= 100 kWc (€/kWh)";
 type: "number_input";
 min_value: 0.0;
 value: number; // default: 0.0761
 step: 0.0001;
 format: "%.4f";
 };

 tarif_oa_bracket_gt100: {
 label: "Barème si P > 100 kWc (€/kWh)";
 type: "number_input";
 min_value: 0.0;
 value: number; // default: 0.0600
 step: 0.0001;
 format: "%.4f";
 };
 };
 };
}
```

### 3. Valorisation de l'Autoconsommation

```typescript
interface AutoconsommationValorisation {
 title: "Valorisation de l'Autoconsommation";

 source_selection: {
 label: "Source pour valoriser l'énergie autoconsommée";
 type: "selectbox";

 options: {
 prix_initial: {
 label: "Prix de vente optimisé (indexé inflation gén.)";
 description: "Utilise le prix de vente calculé avec indexation sur l'inflation générale";
 };

 tarif_edf: {
 label: "Tarif EDF de référence (indexé inflation gén.)";
 description: "Utilise le tarif EDF de référence avec indexation sur l'inflation générale";
 };

 tarif_oa: {
 label: "Tarif d'Obligation d'Achat (selon son indexation)";
 description: "Utilise le tarif OA avec son indexation spécifique";
 };
 };

 default: "prix_initial";
 storage_key: "source_prix_autoconso";
 };
}
```

### 4. Configuration TURPE

```typescript
// Constants from real implementation
const TURPE_PROD_RATES = {
 "BT<=36kVA": {
 "CG": {"Unique": 21.60, "CARD": 22.80},
 "CC": {"Linky": 22.44}
 },
 "BT>36kVA": {
 "CG": {"Unique": 285.96, "CARD": 318.00},
 "CC": {"Mensuelle": 288.84}
 },
 "HTA": {
 "CG": {"Unique": 725.16, "CARD": 725.16},
 "CC": {"Mensuelle": 383.76}
 }
};

interface TURPEConfiguration {
 title: "Paramètres TURPE (Calcul Global)";

 calculation: {
 auto_determination: {
 logic: "Based on total power from all sites";
 rules: {
 if_power_le_36: "BT<=36kVA";
 if_power_le_250: "BT>36kVA";
 if_power_gt_250: "HTA";
 };
 };

 turpe_calculée: {
 type: "metric";
 label: "TURPE Producteur Globale Calculée (€ HT/an)";
 value: string; // Format: "XXX.XX"
 help: string; // "Basé sur P_totale=XX.X kWc et options ci-dessous"

 calculation_formula: "cg_rate + cc_rate";
 };
 };

 configuration: {
 expander_title: " Modifier Options Calcul TURPE Global";

 tension_level: {
 label: "Niveau Tension (basé sur P Totale)";
 type: "selectbox";
 options: ["BT<=36kVA", "BT>36kVA", "HTA"];
 default: "auto_determined";
 storage_key: "turpe_prod_tension";
 };

 contract_type: {
 label: "Type Contrat TURPE";
 type: "selectbox";
 options: ["Unique", "CARD"];
 default: "Unique";
 help: "Contrat Unique ou CARD direct avec Enedis";
 storage_key: "turpe_prod_contrat";
 };

 indexation: {
 label: "Indexer TURPE sur Inflation Générale?";
 type: "checkbox";
 value: boolean; // default: true
 storage_key: "turpe_indexe_inflation";
 };
 };
}
```

### 5. Barèmes Subvention

```typescript
interface SubventionConfiguration {
 title: "Barèmes Subvention (Prime Investissement)";

 configuration: {
 expander_title: " Configuration Barèmes Subvention Globale";

 brackets: {
 subvention_rate_le9: {
 label: "Taux si P <= 9 kWc (€/kWc)";
 type: "number_input";
 value: number; // default: 80.0
 step: 1.0;
 format: "%.1f";
 };

 subvention_rate_le36: {
 label: "Taux si 9 < P <= 36 kWc (€/kWc)";
 type: "number_input";
 value: number; // default: 190.0
 step: 1.0;
 format: "%.1f";
 };

 subvention_rate_le100: {
 label: "Taux si 36 < P <= 100 kWc (€/kWc)";
 type: "number_input";
 value: number; // default: 100.0
 step: 1.0;
 format: "%.1f";
 };

 subvention_rate_le500: {
 label: "Taux si 100 < P <= 500 kWc (€/kWc)";
 type: "number_input";
 value: number; // default: 0.0
 step: 1.0;
 format: "%.1f";
 };
 };
 };

 calculation: {
 subvention_calculée: {
 type: "metric";
 label: "Subvention Totale Projet Calculée (€)";
 value: string; // Format: "X,XXX.XX"
 help: string; // "Basé sur P_totale=XX.X kWc et barèmes ci-dessus"

 calculation_logic: {
 total_power: number; // sum of all sites power
 applicable_rate: number; // determined by brackets
 formula: "applicable_rate * total_power";

 rate_determination: {
 if_power_le_9: "rate_le9";
 if_power_le_36: "rate_le36";
 if_power_le_100: "rate_le100";
 if_power_le_500: "rate_le500";
 };
 };
 };
 };
}
```

## État et Configuration

```typescript
interface EconomietarifsState {
 // Configuration globale stockée dans st.session_state.config
 config: {
 // Paramètres macro-économiques
 taux_inflation: number;
 taux_imposition: number;
 tarif_edf_reference: number;
 source_prix_autoconso: "prix_initial" | "tarif_edf" | "tarif_oa";

 // Tarif OA
 tarif_oa_bracket_le9: number;
 tarif_oa_bracket_le100: number;
 tarif_oa_bracket_gt100: number;
 tarif_oa: number; // Calculé automatiquement
 tarif_oa_indexe_inflation: boolean;
 taux_inflation_tarif_oa: number;

 // TURPE
 turpe_prod_tension: "BT<=36kVA" | "BT>36kVA" | "HTA";
 turpe_prod_contrat: "Unique" | "CARD";
 turpe_prod_calculee: number; // Calculé automatiquement
 turpe_indexe_inflation: boolean;

 // Subvention
 subvention_rate_le9: number;
 subvention_rate_le36: number;
 subvention_rate_le100: number;
 subvention_rate_le500: number;
 subvention_calculee: number; // Calculé automatiquement
 };

 // Configuration par site (pour les calculs totaux)
 sites_config: {
 [site_id: string]: {
 puissance_kwc: number;
 site_type: "Producteur" | "Consommateur Pur";
 //... autres paramètres par site
 };
 };
}
```

## Calculs automatiques

```typescript
interface AutomaticCalculations {
 // Calcul du tarif OA basé sur la puissance totale
 tarif_oa_calculation: {
 function: "default_tarif_oa(p_kwc: float) -> float";
 logic: {
 if_power_le_9: "config.tarif_oa_bracket_le9";
 if_power_le_100: "config.tarif_oa_bracket_le100";
 else: "config.tarif_oa_bracket_gt100";
 };
 total_power_source: "sum(site.puissance_kwc for site in sites_config)";
 };

 // Calcul TURPE
 turpe_calculation: {
 cg_rate: "TURPE_PROD_RATES[tension][CG][contrat]";
 cc_rate: "TURPE_PROD_RATES[tension][CC][first_available_key]";
 total: "cg_rate + cc_rate";

 auto_tension_determination: {
 if_total_power_le_36: "BT<=36kVA";
 if_total_power_le_250: "BT>36kVA";
 else: "HTA";
 };
 };

 // Calcul subvention
 subvention_calculation: {
 total_power: "sum(site.puissance_kwc for site in sites_config)";
 applicable_rate: "determined_by_brackets";
 total_subvention: "applicable_rate * total_power";
 };
}
```

## Exemple d'implémentation Streamlit

```python
import streamlit as st
from modules.config import ConfigModule, default_tarif_oa, TURPE_PROD_RATES

class EconomietarifsTab:
 def __init__(self):
 self.config = st.session_state.config
 self.sites_config = st.session_state.get('sites_config', {})

 def render_macro_economic_params(self):
 """Affiche les paramètres macro-économiques"""
 st.markdown("### Paramètres Macro-économiques")
 col1, col2 = st.columns(2)

 with col1:
 st.session_state.config["taux_inflation"] = st.number_input(
 "Taux d'inflation Général (%)",
 min_value=0.0,
 max_value=10.0,
 value=float(self.config.get("taux_inflation", 2.0)),
 step=0.1,
 help="Inflation annuelle pour OPEX, TURPE (si indexé), prix EDF, etc."
 )

 st.session_state.config["taux_imposition"] = st.number_input(
 "Taux d'imposition Standard (%)",
 min_value=0.0,
 max_value=50.0,
 value=float(self.config.get("taux_imposition", 25.0)),
 step=0.1,
 help="Taux standard appliqué sur la part du bénéfice imposable annuel excédant 42 500€"
 )

 with col2:
 st.session_state.config["tarif_edf_reference"] = st.number_input(
 "Tarif EDF de référence (€/kWh)",
 min_value=0.05,
 max_value=0.50,
 value=float(self.config.get("tarif_edf_reference", 0.21)),
 step=0.01,
 format="%.4f",
 help="Tarif de comparaison pour le gain client"
 )

 def render_tariff_oa_section(self):
 """Affiche la section tarif OA"""
 st.markdown("#### Tarif d'Achat Surplus (OA)")
 col_oa1, col_oa2 = st.columns(2)

 with col_oa1:
 # Calcul du tarif OA basé sur la puissance totale
 current_total_power = sum(cfg.get('puissance_kwc', 0) for cfg in self.sites_config.values())
 calculated_oa = default_tarif_oa(current_total_power) if current_total_power > 0 else 0.0

 st.metric(
 "Tarif OA Applicable (calculé)",
 f"{calculated_oa:.4f} €/kWh",
 help=f"Basé sur P_totale={current_total_power:.1f} kWc et barèmes ci-dessous."
 )

 with col_oa2:
 # Indexation
 index_oa_checkbox = st.checkbox(
 "Indexer le Tarif OA sur Inflation Spécifique?",
 value=self.config.get("tarif_oa_indexe_inflation", True)
 )
 st.session_state.config["tarif_oa_indexe_inflation"] = index_oa_checkbox

 if index_oa_checkbox:
 st.session_state.config["taux_inflation_tarif_oa"] = st.number_input(
 "-> Taux Inflation OA (%)",
 min_value=0.0,
 max_value=10.0,
 value=float(self.config.get("taux_inflation_tarif_oa", 1.89)),
 step=0.1
 )

 # Barèmes en expander
 with st.expander(" Configuration Barèmes Tarif OA"):
 st.session_state.config["tarif_oa_bracket_le9"] = st.number_input(
 "Barème si P <= 9 kWc (€/kWh)",
 min_value=0.0,
 value=float(self.config.get("tarif_oa_bracket_le9", 0.0400)),
 step=0.0001,
 format="%.4f"
 )

 st.session_state.config["tarif_oa_bracket_le100"] = st.number_input(
 "Barème si 9 < P <= 100 kWc (€/kWh)",
 min_value=0.0,
 value=float(self.config.get("tarif_oa_bracket_le100", 0.0761)),
 step=0.0001,
 format="%.4f"
 )

 st.session_state.config["tarif_oa_bracket_gt100"] = st.number_input(
 "Barème si P > 100 kWc (€/kWh)",
 min_value=0.0,
 value=float(self.config.get("tarif_oa_bracket_gt100", 0.0600)),
 step=0.0001,
 format="%.4f"
 )

 def render_turpe_section(self):
 """Affiche la section TURPE"""
 st.markdown("#### Paramètres TURPE (Calcul Global)")

 # Calcul TURPE automatique
 total_power_for_turpe = sum(cfg.get('puissance_kwc', 0) for cfg in self.sites_config.values())

 # Détermination automatique de la tension
 if total_power_for_turpe <= 36:
 default_tension = "BT<=36kVA"
 elif total_power_for_turpe <= 250:
 default_tension = "BT>36kVA"
 else:
 default_tension = "HTA"

 # Calcul du TURPE
 selected_tension = self.config.get("turpe_prod_tension", default_tension)
 selected_contrat = self.config.get("turpe_prod_contrat", "Unique")

 cg_rate = TURPE_PROD_RATES.get(selected_tension, {}).get("CG", {}).get(selected_contrat, 0.0)
 cc_keys = list(TURPE_PROD_RATES.get(selected_tension, {}).get("CC", {}).keys())
 cc_key = cc_keys[0] if cc_keys else None
 cc_rate = TURPE_PROD_RATES.get(selected_tension, {}).get("CC", {}).get(cc_key, 0.0) if cc_key else 0.0

 turpe_glob_calc = cg_rate + cc_rate
 st.session_state.config["turpe_prod_calculee"] = turpe_glob_calc

 st.metric(
 "TURPE Producteur Globale Calculée (€ HT/an)",
 f"{turpe_glob_calc:.2f}",
 help=f"Basé sur P_totale={total_power_for_turpe:.1f} kWc et options ci-dessous."
 )

 # Options de configuration
 with st.expander(" Modifier Options Calcul TURPE Global"):
 col_t1, col_t2 = st.columns(2)

 with col_t1:
 tension_options = list(TURPE_PROD_RATES.keys())
 current_tension_val = self.config.get("turpe_prod_tension", default_tension)
 try:
 current_tension_idx = tension_options.index(current_tension_val)
 except ValueError:
 current_tension_idx = 0
 st.session_state.config["turpe_prod_tension"] = tension_options[0]

 selected_tension_exp = st.selectbox(
 "Niveau Tension (basé sur P Totale)",
 options=tension_options,
 index=current_tension_idx
 )
 st.session_state.config["turpe_prod_tension"] = selected_tension_exp

 with col_t2:
 contrat_options = ["Unique", "CARD"]
 current_contrat_val = self.config.get("turpe_prod_contrat", "Unique")
 try:
 current_contrat_idx = contrat_options.index(current_contrat_val)
 except ValueError:
 current_contrat_idx = 0
 st.session_state.config["turpe_prod_contrat"] = contrat_options[0]

 selected_contrat_exp = st.selectbox(
 "Type Contrat TURPE",
 options=contrat_options,
 index=current_contrat_idx,
 help="Contrat Unique ou CARD direct avec Enedis."
 )
 st.session_state.config["turpe_prod_contrat"] = selected_contrat_exp

 st.session_state.config["turpe_indexe_inflation"] = st.checkbox(
 "Indexer TURPE sur Inflation Générale?",
 value=self.config.get("turpe_indexe_inflation", True)
 )

 def render_subvention_section(self):
 """Affiche la section subvention"""
 st.markdown("#### Barèmes Subvention (Prime Investissement)")

 with st.expander(" Configuration Barèmes Subvention Globale"):
 st.session_state.config["subvention_rate_le9"] = st.number_input(
 "Taux si P <= 9 kWc (€/kWc)",
 value=float(self.config.get("subvention_rate_le9", 80.0)),
 step=1.0,
 format="%.1f"
 )

 st.session_state.config["subvention_rate_le36"] = st.number_input(
 "Taux si 9 < P <= 36 kWc (€/kWc)",
 value=float(self.config.get("subvention_rate_le36", 190.0)),
 step=1.0,
 format="%.1f"
 )

 st.session_state.config["subvention_rate_le100"] = st.number_input(
 "Taux si 36 < P <= 100 kWc (€/kWc)",
 value=float(self.config.get("subvention_rate_le100", 100.0)),
 step=1.0,
 format="%.1f"
 )

 st.session_state.config["subvention_rate_le500"] = st.number_input(
 "Taux si 100 < P <= 500 kWc (€/kWc)",
 value=float(self.config.get("subvention_rate_le500", 0.0)),
 step=1.0,
 format="%.1f"
 )

 # Calcul et affichage de la subvention totale
 total_power_for_sub = sum(cfg.get('puissance_kwc', 0) for cfg in self.sites_config.values())

 # Détermination du taux applicable
 if total_power_for_sub <= 9:
 applicable_rate = float(self.config.get("subvention_rate_le9", 0.0))
 elif total_power_for_sub <= 36:
 applicable_rate = float(self.config.get("subvention_rate_le36", 0.0))
 elif total_power_for_sub <= 100:
 applicable_rate = float(self.config.get("subvention_rate_le100", 0.0))
 elif total_power_for_sub <= 500:
 applicable_rate = float(self.config.get("subvention_rate_le500", 0.0))
 else:
 applicable_rate = 0.0

 total_subvention_glob = applicable_rate * total_power_for_sub
 st.session_state.config["subvention_calculee"] = total_subvention_glob

 st.metric(
 "Subvention Totale Projet Calculée (€)",
 f"{total_subvention_glob:,.2f}",
 help=f"Basé sur P_totale={total_power_for_sub:.1f} kWc et barèmes ci-dessus."
 )

 def render_valorisation_section(self):
 """Affiche la section valorisation autoconsommation"""
 st.markdown("#### Valorisation de l'Autoconsommation")

 source_options = {
 "prix_initial": "Prix de vente optimisé (indexé inflation gén.)",
 "tarif_edf": "Tarif EDF de référence (indexé inflation gén.)",
 "tarif_oa": "Tarif d'Obligation d'Achat (selon son indexation)"
 }

 current_source = self.config.get("source_prix_autoconso", "prix_initial")

 source_prix_selection = st.selectbox(
 "Source pour valoriser l'énergie autoconsommée",
 options=list(source_options.keys()),
 format_func=lambda x: source_options[x],
 index=list(source_options.keys()).index(current_source)
 )

 st.session_state.config["source_prix_autoconso"] = source_prix_selection

 def render_ui(self):
 """Interface principale de l'onglet Économie & Tarifs"""
 st.markdown("<h3 class='sub-header'>Paramètres Macro-économiques & Tarifs</h3>", unsafe_allow_html=True)

 # Paramètres macro-économiques
 self.render_macro_economic_params()

 st.markdown("---")

 # Tarif OA
 self.render_tariff_oa_section()

 st.markdown("---")

 # Valorisation autoconsommation
 self.render_valorisation_section()

 st.markdown("---")

 # TURPE
 self.render_turpe_section()

 st.markdown("---")

 # Subvention
 self.render_subvention_section()

# Utilisation dans l'application principale
def show_economie_tarifs_tab():
 """Fonction appelée par l'onglet Économie & Tarifs"""
 tab = EconomietarifsTab()
 tab.render_ui()
```

## Intégration avec le système multi-sites

L'onglet "Économie & Tarifs" s'intègre parfaitement avec la configuration multi-sites:

- **Calculs automatiques**: Les tarifs OA, TURPE et subventions sont calculés automatiquement basés sur la puissance totale de tous les sites
- **Cohérence globale**: Les paramètres économiques s'appliquent à l'ensemble du projet
- **Réactivité**: Les métriques se mettent à jour automatiquement lors des changements de configuration des sites

## Notes importantes

1. **Calculs temps réel**: Tous les calculs (OA, TURPE, subvention) sont effectués en temps réel basés sur la puissance totale des sites
2. **Indexation différenciée**: Le tarif OA peut avoir sa propre indexation, indépendante de l'inflation générale
3. **Barèmes par paliers**: Les tarifs et subventions suivent des barèmes par paliers de puissance
4. **Intégration financière**: Ces paramètres alimentent directement le moteur de calcul financier d'OptimPV

Cette documentation reflète fidèlement l'implémentation réelle de l'onglet "Économie & Tarifs" dans OptimPV, avec tous les calculs automatiques et l'intégration multi-sites.