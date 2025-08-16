# Configuration Clés de Répartition

## Vue d'ensemble

La page de configuration des clés de répartition permet de définir comment distribuer les coûts, revenus et résultats entre différentes entités dans un projet multi-acteurs: sociétés, filiales, partenaires, ou structures juridiques multiples avec calculs automatiques et validation de cohérence.

## Structure de la page

### Header de Configuration
```typescript
interface RepartitionKeysHeader {
 title: " Clés de Répartition";

 projectStructure: {
 type: "mono_entite" | "multi_entites" | "consortium";

 entities: {
 total: number;
 active: number;

 summary: {
 mainEntity: string;
 partners: number;

 distribution: {
 balanced: boolean;
 majority: string;

 concentration: {
 hhi: number;
 assessment: "dispersed" | "concentrated" | "monopolistic";
 };
 };
 };
 };

 validation: {
 status: "incomplete" | "valid" | "warning" | "error";

 coherence: {
 total: number;
 expected: number;

 balanced: boolean;
 deviation: number;
 };

 issues: ValidationIssue[];
 };
 };

 actions: {
 autoBalance: {
 label: "Équilibrer automatiquement";
 icon: "balance";

 methods: [
 "proportional",
 "equal",
 "weighted",
 "custom"
 ];

 onClick: (method: string) => void;
 };

 template: {
 label: "Templates";
 icon: "folder_copy";

 library: {
 standard: RepartitionTemplate[];
 custom: RepartitionTemplate[];
 };

 actions: {
 load: (template: RepartitionTemplate) => void;
 save: () => void;
 };
 };

 simulate: {
 label: "Simuler répartition";
 icon: "preview";

 scenarios: string[];

 onClick: (scenario: string) => void;
 };
 };
}
```

### Section Entités et Acteurs
```typescript
interface EntitiesSection {
 title: " Entités et acteurs";

 management: {
 entityList: {
 view: "table" | "cards";

 table: {
 columns: [
 {
 id: "name";
 label: "Nom";
 sortable: true;

 cell: {
 editable: boolean;

 validation: {
 required: boolean;
 unique: boolean;
 pattern: RegExp;
 };
 };
 },
 {
 id: "type";
 label: "Type";
 sortable: true;

 cell: {
 type: "select";

 options: [
 { value: "sas", label: "SAS" },
 { value: "sarl", label: "SARL" },
 { value: "sa", label: "SA" },
 { value: "eurl", label: "EURL" },
 { value: "sci", label: "SCI" },
 { value: "particulier", label: "Particulier" },
 { value: "collectivite", label: "Collectivité" }
 ];
 };
 },
 {
 id: "siret";
 label: "SIRET";
 sortable: true;

 cell: {
 validation: {
 format: "siret";
 required: boolean;
 };
 };
 },
 {
 id: "role";
 label: "Rôle";
 sortable: true;

 cell: {
 type: "multi-select";

 options: [
 { value: "investisseur", label: "Investisseur" },
 { value: "exploitant", label: "Exploitant" },
 { value: "proprietaire", label: "Propriétaire" },
 { value: "gestionnaire", label: "Gestionnaire" },
 { value: "prestataire", label: "Prestataire" }
 ];
 };
 },
 {
 id: "participation";
 label: "Participation";
 sortable: true;

 cell: {
 type: "percentage";

 validation: {
 min: 0;
 max: 100;

 coherence: {
 totalCheck: boolean;
 maxTotal: 100;
 };
 };
 };
 },
 {
 id: "status";
 label: "Statut";
 sortable: true;

 cell: {
 type: "badge";

 options: [
 { value: "active", label: "Actif", color: "green" },
 { value: "pending", label: "En attente", color: "orange" },
 { value: "inactive", label: "Inactif", color: "gray" }
 ];
 };
 }
 ];

 data: Entity[];

 actions: {
 add: {
 label: "Ajouter entité";
 icon: "add";

 onClick: () => void;
 };

 import: {
 label: "Importer";
 icon: "upload";

 formats: [".xlsx", ".csv"];

 onImport: (file: File) => void;
 };

 bulk: {
 label: "Actions groupées";

 actions: [
 { id: "activate", label: "Activer" },
 { id: "deactivate", label: "Désactiver" },
 { id: "delete", label: "Supprimer" }
 ];
 };
 };
 };
 };

 entityDetails: {
 selected: string;

 form: {
 identification: {
 label: "Identification";

 fields: {
 name: {
 label: "Dénomination";
 type: "text";
 value: string;
 required: true;
 };

 legalForm: {
 label: "Forme juridique";
 type: "select";
 value: string;

 options: LegalForm[];
 };

 siret: {
 label: "SIRET";
 type: "text";
 value: string;

 validation: {
 format: "siret";

 verification: {
 auto: boolean;

 api: {
 provider: "insee" | "sirene";

 result: {
 valid: boolean;
 data: CompanyData;
 };
 };
 };
 };
 };

 address: {
 label: "Adresse";
 type: "address";
 value: Address;
 };

 contact: {
 label: "Contact";

 fields: {
 person: string;
 email: string;
 phone: string;
 };
 };
 };
 };

 participation: {
 label: "Participation";

 fields: {
 role: {
 label: "Rôle principal";
 type: "select";
 value: string;

 options: [
 {
 value: "investisseur";
 label: "Investisseur";
 description: "Apporte des capitaux";

 implications: [
 "Quote-part investissement",
 "Droits aux revenus",
 "Risques financiers"
 ];
 },
 {
 value: "exploitant";
 label: "Exploitant";
 description: "Gère l'installation";

 implications: [
 "Responsabilité opérationnelle",
 "Frais d'exploitation",
 "Optimisation production"
 ];
 },
 {
 value: "proprietaire";
 label: "Propriétaire";
 description: "Détient les équipements";

 implications: [
 "Propriété juridique",
 "Amortissements",
 "Assurance matériel"
 ];
 }
 ];
 };

 secondaryRoles: {
 label: "Rôles secondaires";
 type: "multi-select";
 value: string[];

 options: SecondaryRole[];
 };

 participation: {
 label: "Taux de participation";
 type: "percentage";
 value: number;

 calculation: {
 basis: "investment" | "revenue" | "ownership" | "custom";

 investment: {
 amount: number;
 percentage: number;
 };

 revenue: {
 entitlement: number;
 percentage: number;
 };

 ownership: {
 shares: number;
 percentage: number;
 };

 custom: {
 formula: string;
 parameters: Parameter[];
 };
 };
 };
 };
 };

 fiscal: {
 label: "Aspects fiscaux";

 fields: {
 regime: {
 label: "Régime fiscal";
 type: "select";
 value: string;

 options: [
 {
 value: "is";
 label: "Impôt sur les sociétés";
 rate: 25;

 implications: [
 "Amortissements déductibles",
 "Report déficits",
 "Intégration fiscale possible"
 ];
 },
 {
 value: "ir";
 label: "Impôt sur le revenu";

 implications: [
 "Transparence fiscale",
 "Déduction immédiate",
 "Plafonnement niches"
 ];
 },
 {
 value: "exonere";
 label: "Exonéré";

 conditions: [
 "Secteur d'activité",
 "Statut juridique",
 "Durée limitée"
 ];
 }
 ];
 };

 tva: {
 label: "TVA";

 assujettissement: {
 type: "select";
 value: string;

 options: [
 { value: "normal", label: "Assujetti normal" },
 { value: "franchise", label: "Franchise en base" },
 { value: "exonere", label: "Exonéré" }
 ];
 };

 taux: {
 applicable: number;

 recuperation: {
 possible: boolean;
 conditions: string[];
 };
 };
 };

 consolidation: {
 label: "Consolidation";

 groupe: {
 membre: boolean;

 integration: {
 fiscale: boolean;
 tva: boolean;

 impacts: [
 "Compensation résultats",
 "Optimisation charges",
 "Facturation interne"
 ];
 };
 };
 };
 };
 };

 contractual: {
 label: "Aspects contractuels";

 fields: {
 agreements: {
 label: "Accords";

 items: [
 {
 type: "shareholders";
 label: "Pacte d'actionnaires";

 status: "draft" | "signed" | "pending";

 clauses: [
 "Répartition dividendes",
 "Droit de préemption",
 "Sortie conjointe"
 ];
 },
 {
 type: "management";
 label: "Convention de gestion";

 status: "draft" | "signed" | "pending";

 clauses: [
 "Responsabilités",
 "Rémunération",
 "Reporting"
 ];
 },
 {
 type: "revenue";
 label: "Accord de répartition";

 status: "draft" | "signed" | "pending";

 clauses: [
 "Clés de répartition",
 "Modalités versement",
 "Résolution conflits"
 ];
 }
 ];
 };

 guarantees: {
 label: "Garanties";

 items: [
 {
 type: "performance";
 label: "Garantie de performance";

 provider: string;
 coverage: number;

 conditions: string[];
 },
 {
 type: "financial";
 label: "Garantie financière";

 provider: string;
 amount: number;

 trigger: string[];
 }
 ];
 };
 };
 };
 };
 };
 };

 relationships: {
 label: "Relations entre entités";

 structure: {
 type: "hierarchy" | "network" | "partnership";

 hierarchy: {
 root: string;

 levels: [
 {
 level: number;
 entities: string[];

 relationships: {
 type: "subsidiary" | "branch" | "participation";
 percentage: number;
 }[];
 }
 ];

 visualization: {
 type: "tree" | "org_chart";

 interactive: boolean;

 details: {
 showPercentages: boolean;
 showRoles: boolean;
 showFinancialFlows: boolean;
 };
 };
 };

 network: {
 nodes: NetworkNode[];
 edges: NetworkEdge[];

 visualization: {
 type: "force" | "circular" | "hierarchical";

 physics: {
 enabled: boolean;

 forces: {
 repulsion: number;
 attraction: number;
 gravity: number;
 };
 };
 };
 };
 };

 flows: {
 label: "Flux financiers";

 types: [
 {
 id: "investment";
 label: "Investissement";

 flows: [
 {
 from: string;
 to: string;
 amount: number;

 conditions: string[];

 timing: {
 schedule: PaymentSchedule;

 milestones: Milestone[];
 };
 }
 ];
 },
 {
 id: "revenue";
 label: "Revenus";

 flows: [
 {
 from: string;
 to: string;

 calculation: {
 basis: "production" | "revenue" | "profit";

 rate: number;

 adjustments: Adjustment[];
 };

 frequency: "monthly" | "quarterly" | "annual";
 }
 ];
 },
 {
 id: "costs";
 label: "Coûts";

 allocation: {
 method: "proportional" | "activity_based" | "fixed";

 categories: CostCategory[];

 rules: AllocationRule[];
 };
 }
 ];
 };
 };
}
```

### Section Définition des Clés
```typescript
interface KeyDefinitionSection {
 title: " Définition des clés";

 categories: {
 investment: {
 label: "Investissement";
 icon: "account_balance";

 method: {
 type: "proportional" | "fixed" | "mixed";

 proportional: {
 basis: "participation" | "capacity" | "usage";

 participation: {
 percentages: {
 [entityId: string]: number;
 };

 validation: {
 total: number;
 balanced: boolean;

 constraints: {
 min: number;
 max: number;
 };
 };
 };

 capacity: {
 basis: "power" | "surface" | "production";

 power: {
 [entityId: string]: {
 allocated: number;
 percentage: number;
 };
 };

 calculation: {
 total: number;

 distribution: {
 automatic: boolean;

 rules: [
 {
 entity: string;
 allocation: number;

 constraints: {
 min?: number;
 max?: number;
 };
 }
 ];
 };
 };
 };
 };

 fixed: {
 amounts: {
 [entityId: string]: number;
 };

 total: number;

 validation: {
 covered: boolean;

 gap: {
 amount: number;
 allocation: "proportional" | "specify";
 };
 };
 };

 mixed: {
 components: [
 {
 type: "fixed";
 amount: number;

 allocation: {
 [entityId: string]: number;
 };
 },
 {
 type: "proportional";
 amount: number;

 basis: "participation";

 allocation: {
 [entityId: string]: number;
 };
 }
 ];

 total: number;

 validation: {
 coherent: boolean;

 components: ComponentValidation[];
 };
 };
 };

 subcategories: {
 capex: {
 label: "CAPEX";

 items: [
 {
 id: "equipment";
 label: "Équipements";
 amount: number;

 allocation: {
 [entityId: string]: number;
 };

 rationale: string;
 },
 {
 id: "installation";
 label: "Installation";
 amount: number;

 allocation: {
 [entityId: string]: number;
 };

 rationale: string;
 },
 {
 id: "development";
 label: "Développement";
 amount: number;

 allocation: {
 [entityId: string]: number;
 };

 rationale: string;
 }
 ];
 };

 working_capital: {
 label: "Besoin en fonds de roulement";

 calculation: {
 method: "percentage" | "detailed";

 percentage: {
 rate: number;

 base: "capex" | "revenue";
 };

 detailed: {
 components: WorkingCapitalComponent[];

 total: number;
 };
 };

 allocation: {
 [entityId: string]: number;
 };
 };

 fees: {
 label: "Frais annexes";

 items: [
 {
 id: "legal";
 label: "Frais juridiques";
 amount: number;

 allocation: {
 method: "equal" | "proportional";

 values: {
 [entityId: string]: number;
 };
 };
 },
 {
 id: "financing";
 label: "Frais de financement";
 amount: number;

 allocation: {
 method: "benefit" | "capacity";

 values: {
 [entityId: string]: number;
 };
 };
 }
 ];
 };
 };
 };

 revenue: {
 label: "Revenus";
 icon: "trending_up";

 sources: [
 {
 id: "electricity_sale";
 label: "Vente d'électricité";

 calculation: {
 basis: "production" | "contract" | "market";

 production: {
 annual: number;

 allocation: {
 method: "ownership" | "capacity" | "investment";

 ownership: {
 [entityId: string]: {
 percentage: number;

 amount: number;
 };
 };
 };
 };

 contract: {
 type: "feed_in" | "ppa" | "self_consumption";

 terms: {
 rate: number;
 duration: number;

 indexation: IndexationConfig;
 };

 allocation: {
 [entityId: string]: {
 entitlement: number;

 conditions: string[];
 };
 };
 };
 };
 },
 {
 id: "green_certificates";
 label: "Certificats verts";

 calculation: {
 basis: "production";

 rate: number;

 market: {
 price: number;

 volatility: number;

 hedging: {
 enabled: boolean;

 strategy: "forward" | "option" | "swap";
 };
 };
 };

 allocation: {
 [entityId: string]: number;
 };
 },
 {
 id: "tax_benefits";
 label: "Avantages fiscaux";

 types: [
 {
 id: "depreciation";
 label: "Amortissements";

 method: "linear" | "declining" | "accelerated";

 allocation: {
 [entityId: string]: {
 basis: number;

 benefit: number;

 timing: number[];
 };
 };
 },
 {
 id: "tax_credit";
 label: "Crédit d'impôt";

 rate: number;

 ceiling: number;

 allocation: {
 [entityId: string]: number;
 };
 }
 ];
 }
 ];

 distribution: {
 frequency: "monthly" | "quarterly" | "annual";

 method: "automatic" | "approval" | "milestone";

 automatic: {
 threshold: number;

 account: {
 type: "individual" | "pooled";

 details: AccountDetails;
 };
 };

 approval: {
 required: string[];

 process: ApprovalProcess;
 };

 milestone: {
 events: MilestoneEvent[];

 conditions: string[];
 };
 };
 };

 costs: {
 label: "Coûts";
 icon: "trending_down";

 categories: [
 {
 id: "operational";
 label: "Coûts opérationnels";

 items: [
 {
 id: "maintenance";
 label: "Maintenance";

 type: "fixed" | "variable";

 fixed: {
 amount: number;

 allocation: {
 method: "equal" | "capacity" | "usage";

 values: {
 [entityId: string]: number;
 };
 };
 };

 variable: {
 rate: number;

 driver: "production" | "capacity" | "time";

 allocation: {
 [entityId: string]: {
 driver_value: number;

 cost: number;
 };
 };
 };
 },
 {
 id: "insurance";
 label: "Assurance";

 premium: number;

 coverage: {
 equipment: boolean;
 liability: boolean;
 business_interruption: boolean;
 };

 allocation: {
 method: "value" | "risk" | "equal";

 values: {
 [entityId: string]: number;
 };
 };
 },
 {
 id: "administration";
 label: "Administration";

 components: [
 {
 name: "Comptabilité";
 amount: number;

 allocation: "equal";
 },
 {
 name: "Juridique";
 amount: number;

 allocation: "proportional";
 },
 {
 name: "Reporting";
 amount: number;

 allocation: "usage";
 }
 ];
 }
 ];
 },
 {
 id: "financial";
 label: "Coûts financiers";

 items: [
 {
 id: "interest";
 label: "Intérêts";

 calculation: {
 basis: "debt_allocation";

 rates: {
 [entityId: string]: {
 debt: number;

 rate: number;

 interest: number;
 };
 };
 };
 },
 {
 id: "fees";
 label: "Commissions";

 types: [
 {
 name: "Arrangement";
 amount: number;

 allocation: "debt_participation";
 },
 {
 name: "Gestion";
 amount: number;

 frequency: "annual";

 allocation: "debt_outstanding";
 }
 ];
 }
 ];
 },
 {
 id: "taxes";
 label: "Fiscalité";

 items: [
 {
 id: "corporate_tax";
 label: "Impôt sociétés";

 calculation: {
 basis: "allocated_profit";

 rates: {
 [entityId: string]: {
 profit: number;

 rate: number;

 tax: number;
 };
 };
 };
 },
 {
 id: "local_taxes";
 label: "Taxes locales";

 types: [
 {
 name: "Taxe foncière";
 amount: number;

 allocation: "ownership";
 },
 {
 name: "CFE";
 amount: number;

 allocation: "activity";
 }
 ];
 }
 ];
 }
 ];
 };
 };

 templates: {
 label: "Templates de répartition";

 library: [
 {
 id: "50_50";
 name: "Répartition égalitaire";

 description: "Répartition 50/50 entre deux entités";

 pattern: {
 entities: 2;

 allocation: {
 investment: [50, 50];
 revenue: [50, 50];
 costs: [50, 50];
 };
 };

 applicability: {
 structures: ["partnership", "joint_venture"];

 conditions: [
 "Apports équivalents",
 "Risques partagés",
 "Gouvernance paritaire"
 ];
 };
 },
 {
 id: "majority_minority";
 name: "Majoritaire/Minoritaire";

 description: "Répartition 70/30 avec contrôle majoritaire";

 pattern: {
 entities: 2;

 allocation: {
 investment: [70, 30];
 revenue: [70, 30];
 costs: [70, 30];
 };

 governance: {
 majority: 0;

 rights: {
 veto: [
 "Investissements majeurs",
 "Changement stratégie",
 "Financement"
 ];
 };
 };
 };
 },
 {
 id: "capacity_based";
 name: "Basé sur la capacité";

 description: "Répartition proportionnelle à la capacité installée";

 pattern: {
 entities: "variable";

 allocation: {
 basis: "installed_capacity";

 method: "proportional";

 adjustments: [
 "Efficacité relative",
 "Coûts spécifiques",
 "Risques techniques"
 ];
 };
 };
 }
 ];

 custom: {
 label: "Templates personnalisés";

 creation: {
 wizard: {
 steps: [
 {
 id: "structure";
 label: "Structure";

 fields: [
 "Nombre d'entités",
 "Type de projet",
 "Objectifs"
 ];
 },
 {
 id: "allocation";
 label: "Répartition";

 fields: [
 "Méthode investissement",
 "Méthode revenus",
 "Méthode coûts"
 ];
 },
 {
 id: "governance";
 label: "Gouvernance";

 fields: [
 "Droits de vote",
 "Prises de décision",
 "Résolution conflits"
 ];
 }
 ];
 };

 validation: {
 coherence: boolean;

 completeness: number;

 warnings: string[];
 };
 };

 sharing: {
 level: "private" | "team" | "public";

 permissions: {
 [userId: string]: "read" | "write" | "admin";
 };
 };
 };
 };
}
```

### Section Simulation et Validation
```typescript
interface SimulationValidationSection {
 title: " Simulation et validation";

 simulation: {
 scenarios: {
 label: "Scénarios de test";

 list: [
 {
 id: "base_case";
 name: "Cas de base";

 parameters: {
 production: number;
 revenue: number;
 costs: number;

 market: {
 electricity_price: number;
 inflation: number;
 discount_rate: number;
 };
 };

 results: {
 [entityId: string]: {
 investment: number;
 revenue: number;
 costs: number;

 netResult: number;

 metrics: {
 roi: number;
 payback: number;
 irr: number;
 };
 };
 };
 },
 {
 id: "optimistic";
 name: "Optimiste";

 parameters: {
 production: number; // +20%
 revenue: number;
 costs: number; // -10%
 };

 results: {
 [entityId: string]: EntityResult;
 };
 },
 {
 id: "pessimistic";
 name: "Pessimiste";

 parameters: {
 production: number; // -20%
 revenue: number;
 costs: number; // +10%
 };

 results: {
 [entityId: string]: EntityResult;
 };
 }
 ];

 comparison: {
 criteria: [
 "Net Result",
 "ROI",
 "Risk",
 "Payback"
 ];

 matrix: {
 [scenario: string]: {
 [entity: string]: {
 [criterion: string]: number;
 };
 };
 };

 visualization: {
 type: "table" | "radar" | "waterfall";

 interactive: boolean;

 export: {
 formats: ["xlsx", "pdf", "csv"];

 onExport: (format: string) => void;
 };
 };
 };
 };

 sensitivity: {
 label: "Analyse de sensibilité";

 parameters: [
 {
 name: "Production";
 range: [-30, 30];
 unit: "%";

 impact: {
 [entityId: string]: {
 revenue: number;
 profit: number;

 sensitivity: number; // % change per % input change
 };
 };
 },
 {
 name: "Prix électricité";
 range: [-50, 50];
 unit: "%";

 impact: {
 [entityId: string]: {
 revenue: number;
 profit: number;

 sensitivity: number;
 };
 };
 },
 {
 name: "Coûts d'exploitation";
 range: [-20, 40];
 unit: "%";

 impact: {
 [entityId: string]: {
 costs: number;
 profit: number;

 sensitivity: number;
 };
 };
 }
 ];

 visualization: {
 type: "tornado" | "spider" | "heatmap";

 ranking: {
 byImpact: SensitivityResult[];

 critical: string[];

 manageable: string[];
 };
 };
 };
 };

 validation: {
 checks: {
 mathematical: {
 label: "Cohérence mathématique";

 rules: [
 {
 id: "allocation_sum";
 name: "Somme des allocations";

 test: "sum(allocations) == 100%";

 status: "passed" | "failed" | "warning";

 result: {
 expected: 100;
 actual: number;

 deviation: number;

 tolerance: number;
 };
 },
 {
 id: "investment_coverage";
 name: "Couverture investissement";

 test: "sum(entity_investments) == total_investment";

 status: "passed" | "failed" | "warning";

 result: {
 expected: number;
 actual: number;

 gap: number;
 };
 }
 ];
 };

 business: {
 label: "Cohérence économique";

 rules: [
 {
 id: "profitability";
 name: "Rentabilité minimale";

 test: "all(entity_roi) >= minimum_roi";

 status: "passed" | "failed" | "warning";

 result: {
 [entityId: string]: {
 roi: number;

 minimum: number;

 meets: boolean;
 };
 };
 },
 {
 id: "risk_balance";
 name: "Équilibre risque/rendement";

 test: "risk_adjusted_return > threshold";

 status: "passed" | "failed" | "warning";

 result: {
 [entityId: string]: {
 risk: number;
 return: number;

 adjustedReturn: number;

 acceptable: boolean;
 };
 };
 }
 ];
 };

 legal: {
 label: "Conformité juridique";

 rules: [
 {
 id: "shareholding_limits";
 name: "Limites de participation";

 test: "all(shareholding) <= legal_limit";

 constraints: [
 {
 type: "foreign_investment";

 limit: number;

 entities: string[];
 },
 {
 type: "concentration";

 limit: number;

 market: string;
 }
 ];
 },
 {
 id: "governance_rights";
 name: "Droits de gouvernance";

 test: "voting_rights consistent with economic_rights";

 analysis: {
 [entityId: string]: {
 economic: number;
 voting: number;

 deviation: number;

 justified: boolean;
 };
 };
 }
 ];
 };
 };

 report: {
 overall: {
 status: "valid" | "warnings" | "errors";

 score: number;

 summary: {
 passed: number;
 warnings: number;
 errors: number;
 };
 };

 details: {
 [category: string]: {
 status: ValidationStatus;

 issues: ValidationIssue[];

 recommendations: string[];
 };
 };

 actions: {
 autoFix: {
 available: boolean;

 fixes: [
 {
 issue: string;

 action: "balance" | "adjust" | "redistribute";

 impact: string;

 onClick: () => void;
 }
 ];
 };

 manual: {
 required: ManualAction[];

 guidance: string[];
 };
 };
 };
 };

 documentation: {
 label: "Documentation";

 generation: {
 automatic: {
 enabled: boolean;

 sections: [
 "Structure du projet",
 "Définition des clés",
 "Simulation financière",
 "Validation des règles"
 ];

 format: "pdf" | "docx" | "html";

 onGenerate: () => void;
 };

 custom: {
 templates: DocumentTemplate[];

 editor: {
 wysiwyg: boolean;

 variables: DocumentVariable[];

 onSave: (content: string) => void;
 };
 };
 };

 export: {
 formats: [
 {
 id: "legal";
 name: "Document juridique";

 format: "pdf";

 content: [
 "Accords de répartition",
 "Annexes techniques",
 "Simulations financières"
 ];
 },
 {
 id: "financial";
 name: "Rapport financier";

 format: "xlsx";

 content: [
 "Tableaux de répartition",
 "Simulations",
 "Analyses de sensibilité"
 ];
 },
 {
 id: "summary";
 name: "Résumé exécutif";

 format: "pptx";

 content: [
 "Structure du projet",
 "Indicateurs clés",
 "Recommandations"
 ];
 }
 ];
 };
 };
}
```

## État et données

```typescript
interface RepartitionKeysState {
 // Entités
 entities: {
 list: Entity[];

 selected: string;

 relationships: {
 structure: EntityStructure;

 flows: FinancialFlow[];

 agreements: Agreement[];
 };
 };

 // Clés de répartition
 keys: {
 investment: AllocationKey;
 revenue: AllocationKey;
 costs: AllocationKey;

 validation: {
 coherent: boolean;

 issues: ValidationIssue[];

 suggestions: string[];
 };
 };

 // Simulation
 simulation: {
 scenarios: SimulationScenario[];

 results: {
 [scenarioId: string]: {
 [entityId: string]: EntityResult;
 };
 };

 sensitivity: SensitivityAnalysis;

 comparison: ComparisonMatrix;
 };

 // Validation
 validation: {
 status: ValidationStatus;

 checks: {
 mathematical: ValidationResult;
 business: ValidationResult;
 legal: ValidationResult;
 };

 report: ValidationReport;
 };

 // Templates
 templates: {
 library: RepartitionTemplate[];
 custom: RepartitionTemplate[];

 current: string;
 };

 // État UI
 ui: {
 activeSection: string;

 entityDetails: {
 visible: boolean;
 entityId: string;
 tab: string;
 };

 simulation: {
 running: boolean;

 parameters: SimulationParameters;

 results: {
 visible: boolean;

 view: "table" | "chart" | "comparison";
 };
 };

 validation: {
 autoCheck: boolean;

 showDetails: boolean;

 autoFix: {
 available: boolean;

 preview: boolean;
 };
 };
 };
}
```

## API Endpoints

```typescript
// Entités
GET /api/entities
POST /api/entities
PUT /api/entities/:id
DELETE /api/entities/:id

// Clés de répartition
GET /api/repartition/keys
PUT /api/repartition/keys
POST /api/repartition/validate

// Simulation
POST /api/repartition/simulate
GET /api/repartition/scenarios
POST /api/repartition/sensitivity

// Templates
GET /api/templates/repartition
POST /api/templates/repartition
PUT /api/templates/repartition/:id

// Documentation
POST /api/repartition/export
GET /api/repartition/documentation
```

## Exemple d'implémentation

```tsx
import React, { useState, useEffect } from 'react';
import {
 RepartitionKeysLayout,
 EntityManager,
 KeyDefinition,
 SimulationPanel,
 ValidationReport
} from '@/components/repartition';

export const RepartitionKeysPage: React.FC = () => {
 const [entities, setEntities] = useState<Entity[]>([]);
 const [keys, setKeys] = useState<AllocationKeys>();
 const [simulation, setSimulation] = useState<SimulationResults>();
 const [validation, setValidation] = useState<ValidationResults>();

 const handleEntityChange = (entityId: string, field: string, value: any) => {
 setEntities(prev =>
 prev.map(entity =>
 entity.id === entityId
? {...entity, [field]: value }
: entity
 )
 );

 // Revalidation automatique
 validateRepartition();
 };

 const handleKeyChange = (category: string, field: string, value: any) => {
 setKeys(prev => ({
...prev,
 [category]: {
...prev[category],
 [field]: value
 }
 }));

 // Recalcul automatique
 recalculateAllocations();
 };

 const runSimulation = async () => {
 const results = await repartitionAPI.simulate({
 entities: entities,
 keys: keys,
 scenarios: simulation.scenarios
 });

 setSimulation(results);
 };

 return (
 <RepartitionKeysLayout>
 <EntityManager
 entities={entities}
 onChange={handleEntityChange}
 onAdd={handleEntityAdd}
 onRemove={handleEntityRemove}
 />

 <KeyDefinition
 keys={keys}
 entities={entities}
 onChange={handleKeyChange}
 validation={validation}
 />

 <SimulationPanel
 entities={entities}
 keys={keys}
 results={simulation}
 onRun={runSimulation}
 />

 <ValidationReport
 validation={validation}
 onAutoFix={handleAutoFix}
 onExport={handleExport}
 />
 </RepartitionKeysLayout>
 );
};
```

Cette configuration des clés de répartition permet une gestion complète des projets multi-acteurs avec validation automatique, simulation financière et génération de documentation juridique.