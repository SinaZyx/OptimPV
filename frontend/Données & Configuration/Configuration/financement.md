# Configuration Financement

## Vue d'ensemble

La page de configuration du financement permet de définir la structure financière du projet photovoltaïque: répartition fonds propres/emprunt, paramètres des prêts, optimisation fiscale, et simulation des différents scenarios de financement pour maximiser la rentabilité.

## Structure de la page

### Header de Configuration
```typescript
interface FinancementHeader {
 title: " Financement";

 summary: {
 investissement: {
 total: number;
 netSubventions: number;
 aFinancer: number;
 };

 structure: {
 fondsPropresPct: number;
 empruntPct: number;
 subventionsPct: number;

 equilibre: boolean;
 warning: string;
 };

 indicateurs: {
 cout: number;
 duree: number;
 mensualite: number;
 };
 };

 actions: {
 optimizer: {
 label: "Optimiser structure";
 icon: "tune";
 onClick: () => void;

 criteria: {
 minimiserCout: boolean;
 maximiserVan: boolean;
 targetTri: number;
 };
 };

 simulator: {
 label: "Simulateur prêt";
 icon: "calculate";
 onClick: () => void;
 };

 compare: {
 label: "Comparer offres";
 icon: "compare";
 onClick: () => void;
 };
 };
}
```

### Section Structure de Financement
```typescript
interface FinancingStructureSection {
 title: " Structure de financement";

 total: {
 label: "Montant total à financer";
 value: number;
 unit: "€ HT";
 readOnly: true;

 breakdown: {
 investissement: number;
 subventions: number;
 net: number;
 };
 };

 components: [
 {
 id: "fonds_propres";
 label: "Fonds propres";
 type: "equity";

 configuration: {
 montant: {
 label: "Montant";
 type: "number";
 value: number;
 unit: "€";

 input: {
 min: 0;
 max: number; // = investissement total
 step: 1000;
 };
 };

 pourcentage: {
 label: "Pourcentage";
 type: "slider";
 value: number;
 unit: "%";

 input: {
 min: 0;
 max: 100;
 step: 5;
 };
 };

 source: {
 label: "Source des fonds";
 type: "select";
 value: string;

 options: [
 {
 value: "tresorerie";
 label: "Trésorerie disponible";
 icon: "account_balance_wallet";

 impact: {
 onLiquidity: "immediate";
 onOpportunity: "medium";
 onRisk: "low";
 };
 },
 {
 value: "augmentation_capital";
 label: "Augmentation de capital";
 icon: "trending_up";

 requirements: [
 "Assemblée générale",
 "Modifications statutaires",
 "Formalités légales"
 ];

 impact: {
 onDilution: "depends";
 onControl: "potential";
 onComplexity: "high";
 };
 },
 {
 value: "compte_courant";
 label: "Compte courant d'associé";
 icon: "person";

 characteristics: {
 flexibility: "high";
 remuneration: "possible";
 recovery: "easy";
 };
 },
 {
 value: "reserve";
 label: "Réserves";
 icon: "savings";

 requirements: [
 "Décision assemblée",
 "Réserves disponibles",
 "Affectation légale"
 ];
 }
 ];
 };

 echeancier: {
 label: "Échéancier d'apport";
 type: "schedule";

 versements: [
 {
 date: Date;
 montant: number;
 pourcentage: number;

 libelle: string;
 statut: "planifie" | "realise" | "retarde";
 }
 ];

 total: {
 montant: number;
 coherence: boolean;
 };
 };
 };

 fiscalite: {
 label: "Aspects fiscaux";

 deductibilite: {
 applicable: boolean;
 conditions: string[];

 impact: {
 immediat: number;
 differe: number;
 };
 };

 plusValue: {
 regime: "normal" | "reduit" | "exonere";
 taux: number;

 optimisation: {
 suggestions: string[];
 potential: number;
 };
 };
 };
 },

 {
 id: "emprunt";
 label: "Emprunt bancaire";
 type: "debt";

 configuration: {
 montant: {
 label: "Montant emprunté";
 type: "number";
 value: number;
 unit: "€";

 validation: {
 min: 0;
 max: number; // = 80% investissement
 optimal: number;
 };
 };

 pourcentage: {
 label: "Pourcentage financé";
 type: "slider";
 value: number;
 unit: "%";

 validation: {
 min: 0;
 max: 80; // Limite bancaire standard

 warnings: {
 tooHigh: "Ratio élevé, négociation difficile";
 tooLow: "Sous-utilisation effet de levier";
 };
 };
 };

 type: {
 label: "Type d'emprunt";
 type: "select";
 value: string;

 options: [
 {
 value: "amortissable";
 label: "Prêt amortissable";
 description: "Remboursement capital + intérêts";

 characteristics: {
 regularite: "Mensualités constantes";
 visibilite: "Complète";
 flexibilite: "Limitée";
 };
 },
 {
 value: "in_fine";
 label: "Prêt in fine";
 description: "Intérêts seuls puis capital final";

 characteristics: {
 cashflow: "Optimisé pendant durée";
 risque: "Refinancement nécessaire";
 fiscalite: "Intérêts déductibles";
 };
 },
 {
 value: "progressif";
 label: "Prêt progressif";
 description: "Mensualités croissantes";

 characteristics: {
 adaptation: "Montée en puissance";
 risque: "Évolution revenus";
 optimisation: "Inflation";
 };
 }
 ];
 };

 taux: {
 label: "Taux d'intérêt";
 type: "number";
 value: number;
 unit: "%";

 structure: {
 type: "fixe" | "variable" | "mixte";

 fixe: {
 taux: number;
 duree: number;

 avantages: [
 "Prévisibilité",
 "Protection hausse",
 "Simplicité"
 ];
 };

 variable: {
 reference: "Euribor" | "Taux BCE" | "Autre";
 marge: number;

 revisions: {
 frequence: "mensuelle" | "trimestrielle" | "annuelle";
 plafond?: number;
 plancher?: number;
 };

 risques: [
 "Variation mensualités",
 "Hausse coût total",
 "Incertitude budgétaire"
 ];
 };
 };

 negociation: {
 elements: [
 {
 item: "Taux de base";
 marge: number;
 negociable: boolean;
 },
 {
 item: "Marge commerciale";
 marge: number;
 negociable: boolean;
 },
 {
 item: "Assurance";
 marge: number;
 negociable: boolean;
 }
 ];

 leviers: [
 "Apport personnel élevé",
 "Garanties additionnelles",
 "Domiciliation produits",
 "Relation bancaire"
 ];
 };
 };

 duree: {
 label: "Durée";
 type: "number";
 value: number;
 unit: "années";

 validation: {
 min: 5;
 max: 20;
 optimal: { min: 10, max: 15 };
 };

 impact: {
 surMensualite: number;
 surCoutTotal: number;
 surRisque: string;
 };

 presets: [
 { label: "7 ans", value: 7, context: "Amortissement rapide" },
 { label: "10 ans", value: 10, context: "Équilibre standard" },
 { label: "15 ans", value: 15, context: "Mensualités réduites" },
 { label: "20 ans", value: 20, context: "Maximum bancaire" }
 ];
 };

 differe: {
 label: "Différé de remboursement";

 enabled: {
 type: "toggle";
 value: boolean;
 label: "Différé activé";
 };

 configuration: {
 duree: {
 label: "Durée du différé";
 type: "number";
 value: number;
 unit: "mois";

 validation: {
 min: 1;
 max: 24;
 };
 };

 type: {
 label: "Type de différé";
 type: "select";
 value: string;

 options: [
 {
 value: "total";
 label: "Différé total";
 description: "Ni capital, ni intérêts";

 impact: {
 cashflow: "Très favorable";
 cout: "Élevé";
 risque: "Capitalisé";
 };
 },
 {
 value: "partiel";
 label: "Différé partiel";
 description: "Intérêts payés, capital différé";

 impact: {
 cashflow: "Favorable";
 cout: "Modéré";
 risque: "Maîtrisé";
 };
 }
 ];
 };
 };

 justification: {
 label: "Justification";
 type: "textarea";
 value: string;

 suggestions: [
 "Temps de montée en puissance",
 "Décalage mise en service",
 "Optimisation trésorerie"
 ];
 };
 };

 garanties: {
 label: "Garanties";
 type: "multi-select";

 options: [
 {
 value: "hypotheque";
 label: "Hypothèque";
 description: "Sûreté réelle sur bien immobilier";

 requirements: [
 "Bien immobilier en propriété",
 "Valeur suffisante",
 "Formalités notariales"
 ];

 impact: {
 onRate: -0.5; // Réduction taux
 onComplexity: "high";
 onRisk: "low";
 };
 },
 {
 value: "nantissement";
 label: "Nantissement";
 description: "Sûreté sur biens mobiliers";

 objects: [
 "Équipements PV",
 "Contrats de vente",
 "Comptes bancaires"
 ];
 },
 {
 value: "caution";
 label: "Caution personnelle";
 description: "Engagement personnel dirigeant";

 types: [
 "Solidaire",
 "Limitée",
 "Avec bénéfice de discussion"
 ];
 },
 {
 value: "assurance";
 label: "Assurance emprunteur";
 description: "Protection décès/invalidité";

 coverage: [
 "Décès",
 "Invalidité",
 "Incapacité temporaire"
 ];
 }
 ];
 };

 frais: {
 label: "Frais annexes";

 items: [
 {
 label: "Frais de dossier";
 type: "number";
 value: number;
 unit: "€";

 calculation: {
 method: "fixe" | "pourcentage";
 base: number;

 negotiation: {
 possible: boolean;
 reduction: number;
 };
 };
 },
 {
 label: "Frais de garantie";
 type: "number";
 value: number;
 unit: "€";

 dependencies: ["hypotheque", "nantissement"];
 },
 {
 label: "Assurance emprunteur";
 type: "number";
 value: number;
 unit: "€/an";

 calculation: {
 rate: number;
 base: "capital_initial" | "capital_restant";
 };
 }
 ];

 total: {
 initial: number;
 annuel: number;

 impact: {
 onTauxEffectif: number;
 onCoutTotal: number;
 };
 };
 };
 };

 simulation: {
 label: "Simulation prêt";

 tableauAmortissement: {
 show: boolean;

 columns: [
 { id: "periode", label: "Période" },
 { id: "capital", label: "Capital" },
 { id: "interets", label: "Intérêts" },
 { id: "mensualite", label: "Mensualité" },
 { id: "restant", label: "Capital restant" }
 ];

 data: AmortizationRow[];

 export: {
 formats: ["excel", "pdf", "csv"];
 onExport: (format: string) => void;
 };
 };

 indicateurs: {
 mensualite: {
 label: "Mensualité";
 value: number;
 unit: "€/mois";

 variation: {
 min: number;
 max: number;
 type: "fixe" | "variable";
 };
 };

 coutTotal: {
 label: "Coût total";
 value: number;
 unit: "€";

 breakdown: {
 capital: number;
 interets: number;
 frais: number;
 };
 };

 tauxEffectif: {
 label: "Taux effectif global";
 value: number;
 unit: "%";

 comparison: {
 tauxNominal: number;
 difference: number;
 };
 };
 };

 sensibilite: {
 label: "Analyse de sensibilité";

 parametres: [
 {
 name: "Taux d'intérêt";
 variation: [-1, 1];
 impact: SensitivityResult;
 },
 {
 name: "Durée";
 variation: [-2, 2];
 impact: SensitivityResult;
 }
 ];

 visualization: {
 type: "tornado" | "table";
 exportable: boolean;
 };
 };
 };
 },

 {
 id: "leasing";
 label: "Crédit-bail";
 type: "lease";
 visible: boolean;

 configuration: {
 montant: {
 label: "Montant financé";
 type: "number";
 value: number;
 unit: "€";
 };

 loyer: {
 label: "Loyer mensuel";
 type: "number";
 value: number;
 unit: "€/mois";

 structure: {
 type: "constant" | "progressif" | "degressif";

 evolution: {
 rate: number;
 frequency: "annuelle" | "trimestrielle";
 };
 };
 };

 duree: {
 label: "Durée";
 type: "number";
 value: number;
 unit: "années";

 validation: {
 min: 3;
 max: 15;
 };
 };

 valeurResiduelle: {
 label: "Valeur résiduelle";
 type: "number";
 value: number;
 unit: "€";

 calculation: {
 method: "pourcentage" | "fixe";
 base: number;

 market: {
 typical: number;
 negotiable: boolean;
 };
 };
 };

 services: {
 label: "Services inclus";

 options: [
 {
 value: "maintenance";
 label: "Maintenance";
 cost: number;
 included: boolean;
 },
 {
 value: "assurance";
 label: "Assurance";
 cost: number;
 included: boolean;
 },
 {
 value: "monitoring";
 label: "Monitoring";
 cost: number;
 included: boolean;
 }
 ];
 };
 };

 avantages: {
 fiscaux: [
 "Loyers déductibles",
 "TVA récupérable",
 "Pas d'immobilisation"
 ];

 operationnels: [
 "Pas d'apport initial",
 "Risque d'obsolescence transféré",
 "Services inclus"
 ];

 financiers: [
 "Préservation capacité d'emprunt",
 "Flexibilité en fin de contrat",
 "Échelonnement des paiements"
 ];
 };

 option: {
 label: "Option en fin de contrat";

 choices: [
 {
 value: "achat";
 label: "Achat";
 price: number;

 decision: {
 criteria: "valeur_marche" | "utilite" | "fiscalite";
 advisable: boolean;
 };
 },
 {
 value: "renouvellement";
 label: "Renouvellement";
 conditions: string;

 duration: number;
 newRate: number;
 },
 {
 value: "restitution";
 label: "Restitution";
 conditions: string;

 responsibilities: [
 "État conforme",
 "Frais de restitution",
 "Remise en état"
 ];
 }
 ];
 };
 },

 {
 id: "subventions";
 label: "Subventions";
 type: "grant";

 montant: {
 label: "Montant total subventions";
 type: "number";
 value: number;
 unit: "€";
 readOnly: true;

 source: "Section subventions";

 detail: {
 nationales: number;
 regionales: number;
 locales: number;
 };
 };

 echeancier: {
 label: "Échéancier des versements";

 versements: [
 {
 organisme: string;
 montant: number;
 date: Date;
 statut: "attendu" | "confirme" | "recu";

 conditions: string[];
 }
 ];

 planning: {
 total: number;
 planifie: number;
 risque: number;
 };
 };

 risques: {
 label: "Gestion des risques";

 identification: [
 {
 type: "non_obtention";
 probabilite: number;
 impact: number;

 mitigation: [
 "Dossier complet",
 "Suivi administratif",
 "Plan B"
 ];
 },
 {
 type: "retard_versement";
 probabilite: number;
 impact: number;

 mitigation: [
 "Trésorerie tampon",
 "Financement pont",
 "Négociation délais"
 ];
 }
 ];

 provisioning: {
 recommended: number;
 applied: number;

 strategy: string;
 };
 };
 }
 ];

 equilibre: {
 label: "Équilibre financier";

 verification: {
 total: number;
 reparti: number;
 equilibre: boolean;

 ecart: {
 montant: number;
 pourcentage: number;
 acceptable: boolean;
 };
 };

 ratios: {
 fondsPropresPct: {
 value: number;
 min: 20;
 optimal: { min: 30, max: 50 };

 assessment: "faible" | "correct" | "eleve";
 };

 endettement: {
 value: number;
 max: 80;

 banque: {
 acceptable: boolean;
 conditions: string[];
 };
 };

 couverture: {
 value: number;
 definition: "Subventions / Investissement";

 impact: {
 onRisk: number;
 onReturn: number;
 };
 };
 };
 };
}
```

### Section Optimisation Financière
```typescript
interface OptimizationSection {
 title: " Optimisation financière";

 objectifs: {
 label: "Objectifs d'optimisation";

 criteres: [
 {
 id: "minimiser_cout";
 label: "Minimiser le coût total";
 weight: number;
 priority: "high" | "medium" | "low";

 metrics: {
 current: number;
 target: number;
 potential: number;
 };
 },
 {
 id: "maximiser_van";
 label: "Maximiser la VAN";
 weight: number;
 priority: "high" | "medium" | "low";

 metrics: {
 current: number;
 target: number;
 potential: number;
 };
 },
 {
 id: "target_tri";
 label: "Atteindre TRI cible";
 weight: number;
 priority: "high" | "medium" | "low";

 target: {
 value: number;
 current: number;
 achievable: boolean;
 };
 },
 {
 id: "optimiser_fiscalite";
 label: "Optimiser fiscalité";
 weight: number;
 priority: "high" | "medium" | "low";

 opportunities: OptimizationOpportunity[];
 }
 ];
 };

 scenarios: {
 label: "Scénarios de financement";

 list: [
 {
 id: "scenario_1";
 name: "Financement mixte équilibré";

 structure: {
 fondsPropresPct: 40;
 empruntPct: 60;
 subventionsPct: 15;
 };

 parameters: {
 tauxEmprunt: 3.5;
 dureeEmprunt: 12;
 garanties: ["nantissement"];
 };

 results: {
 coutTotal: number;
 van: number;
 tri: number;
 payback: number;

 cashflow: {
 initial: number;
 monthly: number;
 annual: number[];
 };
 };

 assessment: {
 score: number;
 advantages: string[];
 drawbacks: string[];

 recommendation: "optimal" | "acceptable" | "deconseille";
 };
 },
 {
 id: "scenario_2";
 name: "Financement par emprunt maximal";

 structure: {
 fondsPropresPct: 20;
 empruntPct: 80;
 subventionsPct: 15;
 };

 parameters: {
 tauxEmprunt: 4.0;
 dureeEmprunt: 15;
 garanties: ["hypotheque", "caution"];
 };

 results: {
 coutTotal: number;
 van: number;
 tri: number;
 payback: number;

 cashflow: {
 initial: number;
 monthly: number;
 annual: number[];
 };
 };

 assessment: {
 score: number;
 advantages: string[];
 drawbacks: string[];

 recommendation: "optimal" | "acceptable" | "deconseille";
 };
 }
 ];

 comparison: {
 criteria: string[];
 matrix: ComparisonMatrix;

 recommendation: {
 best: string;
 reasoning: string;

 sensitivity: {
 robust: boolean;
 conditions: string[];
 };
 };
 };
 };

 optimisations: {
 label: "Optimisations fiscales";

 opportunities: [
 {
 id: "amortissement_degressif";
 label: "Amortissement dégressif";

 description: "Accélération des amortissements";

 conditions: [
 "Matériel neuf",
 "Durée ≥ 3 ans",
 "Éligibilité équipement"
 ];

 impact: {
 year1: number;
 year2: number;
 year3: number;

 totalBenefit: number;
 netPresentValue: number;
 };

 implementation: {
 complexity: "low" | "medium" | "high";
 cost: number;
 timeline: string;
 };
 },
 {
 id: "suramortissement";
 label: "Suramortissement";

 description: "Déduction exceptionnelle 40%";

 conditions: [
 "Équipement neuf",
 "Acquisition avant 31/12/2024",
 "Affectation exploitation"
 ];

 impact: {
 deduction: number;
 economie: number;

 timing: {
 immediate: boolean;
 year: number;
 };
 };

 eligibility: {
 equipment: boolean;
 timeline: boolean;
 conditions: boolean;
 };
 },
 {
 id: "credit_impot";
 label: "Crédit d'impôt recherche";

 description: "CIR pour innovation";

 conditions: [
 "Dépenses R&D",
 "Innovation technique",
 "Documentation"
 ];

 impact: {
 rate: 30; // %
 maxAmount: number;

 recovery: {
 immediate: boolean;
 refund: boolean;
 };
 };

 application: {
 eligible: boolean;
 amount: number;

 requirements: string[];
 };
 }
 ];

 simulation: {
 withOptimization: {
 fiscalite: number;
 netResult: number;

 timeline: {
 year: number;
 savings: number;
 }[];
 };

 withoutOptimization: {
 fiscalite: number;
 netResult: number;
 };

 benefit: {
 annual: number;
 cumulative: number;

 roi: {
 implementation: number;
 payback: number;
 };
 };
 };
 };
}
```

## État et données

```typescript
interface FinancementState {
 // Structure financière
 structure: {
 total: number;
 components: FinancingComponent[];

 equilibre: {
 balanced: boolean;
 gap: number;
 warnings: string[];
 };
 };

 // Configuration emprunts
 debt: {
 amount: number;
 rate: number;
 duration: number;
 type: LoanType;

 guarantees: Guarantee[];
 fees: LoanFee[];

 simulation: {
 monthlyPayment: number;
 totalCost: number;
 effectiveRate: number;

 amortization: AmortizationRow[];
 };
 };

 // Leasing
 lease: {
 enabled: boolean;
 amount: number;
 monthlyPayment: number;
 duration: number;
 residualValue: number;

 services: LeaseService[];

 comparison: {
 withPurchase: ComparisonResult;
 recommendation: string;
 };
 };

 // Optimisation
 optimization: {
 objectives: OptimizationObjective[];
 scenarios: FinancingScenario[];

 fiscal: {
 opportunities: FiscalOpportunity[];
 simulation: FiscalSimulation;
 };

 recommendation: {
 best: string;
 reasoning: string;
 sensitivity: SensitivityAnalysis;
 };
 };

 // Calculs
 calculations: {
 totalCost: number;
 monthlyPayment: number;
 effectiveRate: number;

 ratios: {
 debtToEquity: number;
 debtService: number;
 coverage: number;
 };

 cashflow: {
 initial: number;
 monthly: number;
 annual: number[];
 };
 };

 // État UI
 ui: {
 activeTab: string;
 showAdvanced: boolean;

 modals: {
 loanSimulator: boolean;
 scenarioComparison: boolean;
 fiscalOptimization: boolean;
 };

 loading: {
 simulation: boolean;
 optimization: boolean;
 };
 };
}
```

## API Endpoints

```typescript
// Simulation prêt
POST /api/financing/loan/simulate
Body: {
 amount: number;
 rate: number;
 duration: number;
 type: LoanType;
 defer?: DeferConfig;
}

// Optimisation structure
POST /api/financing/optimize
Body: {
 investment: number;
 constraints: Constraint[];
 objectives: Objective[];

 market: {
 rates: MarketRate[];
 conditions: MarketCondition[];
 };
}

// Opportunités fiscales
GET /api/tax/opportunities
Query: {
 investment: number;
 structure: string;
 sector: string;
 region: string;
}

// Comparaison scénarios
POST /api/financing/scenarios/compare
Body: {
 scenarios: FinancingScenario[];
 criteria: string[];
 weights: number[];
}
```

## Exemple d'implémentation

```tsx
import React, { useState, useEffect } from 'react';
import {
 FinancementLayout,
 StructureConfiguration,
 LoanSimulator,
 OptimizationPanel,
 ScenarioComparison
} from '@/components/financing';

export const FinancementPage: React.FC = () => {
 const [structure, setStructure] = useState<FinancingStructure>();
 const [optimization, setOptimization] = useState<OptimizationResults>();
 const [scenarios, setScenarios] = useState<FinancingScenario[]>();

 const handleStructureChange = (component: string, field: string, value: any) => {
 setStructure(prev => ({
...prev,
 components: prev.components.map(comp =>
 comp.id === component
? {...comp, [field]: value }
: comp
 )
 }));

 // Recalcul automatique
 recalculateFinancing();
 };

 const optimizeStructure = async () => {
 const results = await financingAPI.optimize({
 investment: projectData.investment,
 constraints: structure.constraints,
 objectives: optimization.objectives
 });

 setOptimization(results);
 setScenarios(results.scenarios);
 };

 return (
 <FinancementLayout>
 <StructureConfiguration
 structure={structure}
 onChange={handleStructureChange}
 validation={validation}
 />

 <LoanSimulator
 config={structure?.debt}
 onSimulate={handleLoanSimulation}
 />

 <OptimizationPanel
 objectives={optimization?.objectives}
 opportunities={optimization?.fiscal}
 onOptimize={optimizeStructure}
 />

 <ScenarioComparison
 scenarios={scenarios}
 recommendation={optimization?.recommendation}
 />
 </FinancementLayout>
 );
};
```

Cette configuration de financement offre une approche complète et optimisée pour structurer le financement du projet photovoltaïque avec tous les outils nécessaires à la décision.