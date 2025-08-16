# Page Configuration - Module Facturation

## Vue d'ensemble

La page Configuration du module Facturation permet de paramétrer tous les aspects de la facturation: informations société, templates, règles de calcul, automatisations et intégrations.

## Structure de la page

### Header Principal
```typescript
interface FacturationConfigHeader {
 title: " Configuration Facturation";

 breadcrumb: [
 { label: "Facturation", link: "/facturation" },
 { label: "Configuration", active: true }
 ];

 actions: {
 save: {
 label: " Enregistrer";
 onClick: () => void;
 loading: boolean;
 hasChanges: boolean;
 };

 testConfig: {
 label: " Tester configuration";
 onClick: () => void;
 tooltip: "Générer une facture test";
 };

 export: {
 label: " Exporter config";
 onClick: () => void;
 };
 };
}
```

### Navigation par Sections
```typescript
interface ConfigSections {
 navigation: {
 style: "vertical-tabs" | "accordion";

 sections: [
 {
 id: "company";
 label: " Informations Société";
 icon: "business";
 hasErrors: boolean;
 },
 {
 id: "invoicing";
 label: " Paramètres Facturation";
 icon: "receipt";
 hasErrors: boolean;
 },
 {
 id: "templates";
 label: " Templates & Documents";
 icon: "description";
 badge?: number; // Nombre de templates
 },
 {
 id: "calculations";
 label: " Règles de Calcul";
 icon: "calculate";
 advanced: true;
 },
 {
 id: "automation";
 label: " Automatisations";
 icon: "smart_toy";
 badge?: "new";
 },
 {
 id: "integrations";
 label: " Intégrations";
 icon: "link";
 badge?: number; // Actives
 },
 {
 id: "notifications";
 label: " Notifications";
 icon: "notifications";
 }
 ];
 };

 activeSection: string;
}
```

### Section Informations Société
```typescript
interface CompanyInfoSection {
 title: " Informations Société";
 description: "Informations légales qui apparaîtront sur les factures";

 form: {
 general: {
 title: "Informations Générales";

 fields: {
 companyName: {
 label: "Raison sociale";
 type: "text";
 required: true;
 maxLength: 100;
 validation: "not-empty";
 };

 legalForm: {
 label: "Forme juridique";
 type: "select";
 options: ["SAS", "SARL", "SA", "SCI", "Association", "Autre"];
 required: true;
 };

 registrationNumber: {
 label: "SIRET";
 type: "text";
 pattern: /^\d{14}$/;
 validation: "siret";
 help: "14 chiffres";
 };

 vatNumber: {
 label: "N° TVA Intracommunautaire";
 type: "text";
 pattern: /^FR\d{11}$/;
 validation: "vat-fr";
 placeholder: "FR12345678901";
 };

 capital: {
 label: "Capital social";
 type: "currency";
 suffix: "€";
 help: "Pour mentions légales";
 };
 };
 };

 contact: {
 title: "Coordonnées";

 fields: {
 address: {
 label: "Adresse";
 type: "address";
 required: true;
 components: {
 street: string;
 postalCode: string;
 city: string;
 country: string;
 };
 };

 phone: {
 label: "Téléphone";
 type: "tel";
 validation: "phone-fr";
 };

 email: {
 label: "Email";
 type: "email";
 required: true;
 validation: "email";
 };

 website: {
 label: "Site web";
 type: "url";
 validation: "url";
 };
 };
 };

 banking: {
 title: "Informations Bancaires";

 fields: {
 bankName: {
 label: "Banque";
 type: "text";
 };

 iban: {
 label: "IBAN";
 type: "iban";
 required: true;
 validation: "iban";
 mask: true;
 };

 bic: {
 label: "BIC/SWIFT";
 type: "text";
 pattern: /^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$/;
 };

 accountHolder: {
 label: "Titulaire du compte";
 type: "text";
 placeholder: "Si différent de la société";
 };
 };
 };

 branding: {
 title: "Identité Visuelle";

 fields: {
 logo: {
 label: "Logo";
 type: "file-upload";
 accept: ["image/png", "image/jpeg", "image/svg+xml"];
 maxSize: 2; // MB
 preview: true;

 recommendations: [
 "Format: PNG ou SVG recommandé",
 "Taille: 500x200px minimum",
 "Fond transparent préférable"
 ];
 };

 primaryColor: {
 label: "Couleur principale";
 type: "color";
 default: "#2196F3";
 };

 secondaryColor: {
 label: "Couleur secondaire";
 type: "color";
 default: "#FF9800";
 };

 signature: {
 label: "Signature";
 type: "file-upload";
 accept: ["image/png", "image/jpeg"];
 maxSize: 1;
 help: "Signature du responsable";
 };
 };
 };
 };
}
```

### Section Paramètres Facturation
```typescript
interface InvoicingSettingsSection {
 title: " Paramètres de Facturation";

 subsections: {
 numbering: {
 title: "Numérotation des Factures";

 fields: {
 format: {
 label: "Format de numérotation";
 type: "pattern-builder";
 value: string; // Ex: "FAC-{YYYY}-{MM}-{0000}"

 variables: [
 { code: "{YYYY}", label: "Année" },
 { code: "{YY}", label: "Année courte" },
 { code: "{MM}", label: "Mois" },
 { code: "{DD}", label: "Jour" },
 { code: "{0000}", label: "Compteur" },
 { code: "{PROJECT}", label: "Code projet" }
 ];

 preview: string; // "FAC-2024-03-0001"
 };

 counter: {
 label: "Prochain numéro";
 type: "number";
 min: 1;
 help: "Compteur actuel: 245";
 };

 resetPeriod: {
 label: "Réinitialisation compteur";
 type: "select";
 options: [
 { value: "never", label: "Jamais" },
 { value: "yearly", label: "Chaque année" },
 { value: "monthly", label: "Chaque mois" }
 ];
 };

 creditNoteFormat: {
 label: "Format des avoirs";
 type: "pattern-builder";
 value: string; // "AV-{YYYY}-{0000}"
 };
 };
 };

 defaults: {
 title: "Valeurs par Défaut";

 fields: {
 currency: {
 label: "Devise";
 type: "select";
 options: ["EUR", "USD", "GBP", "CHF"];
 default: "EUR";
 };

 language: {
 label: "Langue des documents";
 type: "select";
 options: [
 { value: "fr", label: "Français" },
 { value: "en", label: "Anglais" },
 { value: "es", label: "Espagnol" }
 ];
 default: "fr";
 };

 paymentTerms: {
 label: "Délai de paiement (jours)";
 type: "number";
 min: 0;
 max: 90;
 default: 30;
 suffix: "jours";
 };

 latePaymentRate: {
 label: "Taux pénalités de retard";
 type: "number";
 min: 0;
 max: 20;
 step: 0.1;
 default: 10;
 suffix: "%";
 help: "Taux annuel légal: 10%";
 };

 discountRate: {
 label: "Escompte paiement anticipé";
 type: "number";
 min: 0;
 max: 5;
 step: 0.1;
 default: 0;
 suffix: "%";
 };
 };
 };

 taxes: {
 title: "TVA et Taxes";

 fields: {
 defaultVatRate: {
 label: "Taux TVA par défaut";
 type: "select";
 options: [
 { value: 20, label: "20% (Taux normal)" },
 { value: 10, label: "10% (Taux intermédiaire)" },
 { value: 5.5, label: "5.5% (Taux réduit)" },
 { value: 2.1, label: "2.1% (Taux super-réduit)" },
 { value: 0, label: "0% (Exonéré)" }
 ];
 default: 20;
 };

 vatMode: {
 label: "Mode TVA";
 type: "radio";
 options: [
 { value: "standard", label: "TVA sur les débits" },
 { value: "cash", label: "TVA sur encaissements" }
 ];
 help: "Selon votre régime fiscal";
 };

 vatExemptionText: {
 label: "Mention exonération TVA";
 type: "textarea";
 visible: (vatRate: number) => vatRate === 0;
 placeholder: "Article 293 B du CGI";
 };

 otherTaxes: {
 label: "Autres taxes";
 type: "dynamic-list";
 items: Array<{
 name: string;
 rate: number;
 base: "ht" | "ttc";
 }>;
 };
 };
 };
 };
}
```

### Section Templates Documents
```typescript
interface DocumentTemplatesSection {
 title: " Templates et Documents";

 templateManager: {
 categories: [
 {
 id: "invoices";
 label: "Factures";
 icon: "receipt";
 templates: Array<{
 id: string;
 name: string;
 description: string;
 isDefault: boolean;
 lastModified: Date;
 preview: string; // URL

 actions: {
 edit: () => void;
 duplicate: () => void;
 setDefault: () => void;
 delete: () => void;
 preview: () => void;
 };
 }>;
 },
 {
 id: "credit_notes";
 label: "Avoirs";
 icon: "receipt_long";
 templates: Template[];
 },
 {
 id: "quotes";
 label: "Devis";
 icon: "request_quote";
 templates: Template[];
 },
 {
 id: "reminders";
 label: "Relances";
 icon: "mail";
 templates: Template[];
 }
 ];

 editor: {
 visible: boolean;
 template: Template | null;

 tools: {
 variables: {
 categories: [
 {
 name: "Société";
 vars: ["{company_name}", "{vat_number}", "{address}"];
 },
 {
 name: "Client";
 vars: ["{client_name}", "{client_address}", "{client_email}"];
 },
 {
 name: "Facture";
 vars: ["{invoice_number}", "{invoice_date}", "{due_date}"];
 },
 {
 name: "Montants";
 vars: ["{subtotal}", "{vat_amount}", "{total}"];
 }
 ];
 };

 blocks: {
 available: [
 "Header",
 "Client Info",
 "Invoice Details",
 "Line Items",
 "Totals",
 "Payment Info",
 "Footer"
 ];
 };

 styling: {
 fonts: string[];
 colors: string[];
 layouts: ["Classic", "Modern", "Minimal"];
 };
 };

 preview: {
 mode: "live" | "pdf";
 sampleData: boolean;
 zoom: number;
 };
 };
 };

 documentSettings: {
 title: "Paramètres Documents";

 fields: {
 paperSize: {
 label: "Format papier";
 type: "select";
 options: ["A4", "Letter", "Legal"];
 default: "A4";
 };

 margins: {
 label: "Marges (mm)";
 type: "quad-input";
 values: {
 top: number;
 right: number;
 bottom: number;
 left: number;
 };
 };

 footerText: {
 label: "Texte pied de page";
 type: "rich-text";
 maxLength: 500;
 variables: true;
 };

 legalMentions: {
 label: "Mentions légales";
 type: "rich-text";
 required: true;
 templates: [
 "Mentions standard SAS",
 "Mentions association",
 "Personnalisé"
 ];
 };
 };
 };
}
```

### Section Règles de Calcul
```typescript
interface CalculationRulesSection {
 title: " Règles de Calcul";
 warning: "Modification réservée aux utilisateurs avancés";

 rules: {
 rounding: {
 title: "Arrondis";

 fields: {
 itemRounding: {
 label: "Arrondi lignes facture";
 type: "select";
 options: [
 { value: 2, label: "2 décimales (0.01€)" },
 { value: 3, label: "3 décimales (0.001€)" },
 { value: 4, label: "4 décimales (0.0001€)" }
 ];
 default: 2;
 };

 totalRounding: {
 label: "Arrondi totaux";
 type: "select";
 options: [
 { value: "mathematical", label: "Mathématique (0.5 → 1)" },
 { value: "down", label: "Inférieur" },
 { value: "up", label: "Supérieur" }
 ];
 };

 vatCalculation: {
 label: "Calcul TVA";
 type: "radio";
 options: [
 { value: "per_line", label: "Par ligne" },
 { value: "on_total", label: "Sur le total" }
 ];
 help: "Impact sur les arrondis TVA";
 };
 };
 };

 pricing: {
 title: "Tarification";

 fields: {
 priceSource: {
 label: "Source des prix";
 type: "select";
 options: [
 "Prix négocié participant",
 "Grille tarifaire projet",
 "Prix spot + marge",
 "Formule personnalisée"
 ];
 };

 marginCalculation: {
 label: "Calcul des marges";
 type: "formula-editor";
 value: string;
 variables: ["cost", "market_price", "volume"];

 examples: [
 "cost * 1.15",
 "market_price * 0.95",
 "cost + (volume > 1000? 0.01: 0.02)"
 ];
 };

 minimumInvoiceAmount: {
 label: "Montant minimum facture";
 type: "currency";
 min: 0;
 default: 0;
 help: "Factures < montant min non générées";
 };
 };
 };

 allocations: {
 title: "Répartitions";

 fields: {
 allocationMethod: {
 label: "Méthode de répartition";
 type: "select";
 options: [
 "Clés fixes",
 "Consommation réelle",
 "Production au prorata",
 "Hybride"
 ];
 };

 roundingCompensation: {
 label: "Compensation arrondis";
 type: "select";
 options: [
 "Sur le plus gros consommateur",
 "Répartition proportionnelle",
 "Report période suivante"
 ];
 };
 };
 };
 };
}
```

### Section Automatisations
```typescript
interface AutomationSection {
 title: " Automatisations";

 workflows: Array<{
 id: string;
 name: string;
 active: boolean;

 trigger: {
 type: "schedule" | "event" | "manual";
 config: {
 schedule?: {
 frequency: "daily" | "weekly" | "monthly";
 time: string;
 dayOfMonth?: number;
 };
 event?: {
 type: string;
 conditions: any[];
 };
 };
 };

 actions: Array<{
 type: "generate_invoices" | "send_invoices" | "send_reminders" | "export_accounting";
 config: any;
 conditions?: any[];
 }>;

 history: {
 lastRun?: Date;
 nextRun?: Date;
 successCount: number;
 errorCount: number;
 };

 controls: {
 toggle: () => void;
 edit: () => void;
 test: () => void;
 viewLogs: () => void;
 };
 }>;

 addWorkflow: {
 button: "Créer automatisation";
 templates: [
 "Facturation mensuelle automatique",
 "Relances progressives",
 "Export comptable mensuel",
 "Notification impayés"
 ];
 };
}
```

## État et données

```typescript
interface FacturationConfigState {
 // Configuration
 config: {
 company: CompanyInfo;
 invoicing: InvoicingSettings;
 templates: DocumentTemplate[];
 calculations: CalculationRules;
 automations: AutomationWorkflow[];
 integrations: Integration[];
 notifications: NotificationSettings;
 };

 // État
 state: {
 hasChanges: boolean;
 errors: ValidationError[];
 activeSection: string;
 saving: boolean;
 };

 // UI
 ui: {
 editingTemplate: string | null;
 testMode: boolean;
 expandedSections: string[];
 };
}
```

## Exemple d'implémentation

```tsx
export const FacturationConfigPage: React.FC = () => {
 const [activeSection, setActiveSection] = useState("company");
 const [hasChanges, setHasChanges] = useState(false);
 const { config, updateConfig, saveConfig, testConfig } = useFacturationConfig();

 const handleSave = async () => {
 const validation = validateConfig(config);
 if (validation.isValid) {
 await saveConfig(config);
 notification.success("Configuration sauvegardée");
 setHasChanges(false);
 }
 };

 return (
 <ConfigLayout>
 <FacturationConfigHeader
 hasChanges={hasChanges}
 onSave={handleSave}
 onTest={() => testConfig(config)}
 />

 <Grid container spacing={3}>
 <Grid item xs={12} md={3}>
 <ConfigNavigation
 sections={configSections}
 activeSection={activeSection}
 onChange={setActiveSection}
 />
 </Grid>

 <Grid item xs={12} md={9}>
 <ConfigContent>
 {activeSection === "company" && (
 <CompanyInfoSection
 data={config.company}
 onChange={(data) => updateSection("company", data)}
 />
 )}

 {activeSection === "invoicing" && (
 <InvoicingSettingsSection
 data={config.invoicing}
 onChange={(data) => updateSection("invoicing", data)}
 />
 )}

 {activeSection === "templates" && (
 <DocumentTemplatesSection
 templates={config.templates}
 onUpdate={(templates) => updateSection("templates", templates)}
 />
 )}

 {/* Autres sections... */}
 </ConfigContent>
 </Grid>
 </Grid>
 </ConfigLayout>
 );
};
```