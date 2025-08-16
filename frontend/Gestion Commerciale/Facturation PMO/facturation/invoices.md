# Page Génération et Gestion des Factures - Module Facturation

## Vue d'ensemble

La page Factures permet de générer, gérer et suivre toutes les factures liées aux projets d'autoconsommation collective.

## Structure de la page

### Header Principal
```typescript
interface InvoicesHeader {
 title: " Gestion des Factures";

 stats: {
 pendingGeneration: number;
 awaitingPayment: number;
 totalThisMonth: number;
 collectionRate: number; // %
 };

 actions: {
 generateInvoices: {
 label: " Générer factures mensuelles";
 onClick: () => void;
 variant: "primary";
 badge?: number; // Nombre à générer
 };

 batchActions: {
 label: "Actions groupées";
 options: [
 "Envoyer par email",
 "Télécharger ZIP",
 "Marquer comme envoyées",
 "Générer avoirs"
 ];
 onSelect: (action: string) => void;
 };
 };
}
```

### Section Génération de Factures
```typescript
interface InvoiceGeneration {
 wizard: {
 currentStep: number;
 steps: [
 {
 id: "selection";
 title: "Sélection";
 description: "Choisir les projets et participants";
 },
 {
 id: "period";
 title: "Période";
 description: "Définir la période de facturation";
 },
 {
 id: "preview";
 title: "Aperçu";
 description: "Vérifier avant génération";
 },
 {
 id: "generation";
 title: "Génération";
 description: "Créer les factures";
 }
 ];
 };

 step1_selection: {
 projects: {
 title: "Projets à facturer";
 mode: "checkbox" | "all";

 list: Array<{
 id: string;
 name: string;
 participants: number;
 ready: boolean;
 issues?: string[];
 lastInvoiced: Date;
 }>;

 filters: {
 status: ["Actif", "En pause", "Tous"];
 hasData: boolean;
 overdue: boolean;
 };
 };

 participants: {
 title: "Participants";
 selectAll: boolean;

 filters: {
 withBalance: boolean;
 activeOnly: boolean;
 customSelection: string[];
 };

 preview: {
 total: number;
 excluded: number;
 reasons: string[];
 };
 };
 };

 step2_period: {
 periodType: {
 label: "Type de période";
 options: [
 { value: "monthly", label: "Mensuelle", default: true },
 { value: "quarterly", label: "Trimestrielle" },
 { value: "annual", label: "Annuelle" },
 { value: "custom", label: "Personnalisée" }
 ];
 };

 monthSelection: {
 visible: boolean; // Si mensuelle
 value: string; // "YYYY-MM"
 availableMonths: string[];
 lastInvoiced: Record<string, Date>;
 };

 customPeriod: {
 visible: boolean; // Si personnalisée
 startDate: Date;
 endDate: Date;
 validation: string[];
 };

 options: {
 prorata: {
 label: "Appliquer prorata temporis";
 enabled: boolean;
 help: "Pour les participants arrivés/partis en cours";
 };

 includeAdjustments: {
 label: "Inclure les ajustements";
 enabled: boolean;
 types: ["Régularisations", "Avoirs", "Pénalités"];
 };
 };
 };

 step3_preview: {
 summary: {
 title: "Résumé de génération";

 metrics: {
 invoiceCount: number;
 totalAmount: number;
 averageAmount: number;
 period: string;
 };

 breakdown: {
 byProject: Record<string, {
 count: number;
 amount: number;
 }>;

 byType: {
 standard: number;
 adjustment: number;
 credit: number;
 };
 };
 };

 preview: {
 title: "Aperçu des factures";

 table: {
 columns: ["Participant", "Projet", "Montant HT", "TVA", "TTC", "Statut"];
 data: Array<{
 participant: string;
 project: string;
 amounts: {
 ht: number;
 tva: number;
 ttc: number;
 };
 status: "OK" | "Warning" | "Error";
 details?: string;
 }>;

 actions: {
 viewDetail: (id: string) => void;
 exclude: (id: string) => void;
 adjust: (id: string) => void;
 };
 };

 issues: {
 title: "Points d'attention";
 items: Array<{
 severity: "error" | "warning" | "info";
 participant: string;
 message: string;
 action?: () => void;
 }>;
 };
 };
 };

 step4_generation: {
 progress: {
 title: "Génération en cours...";

 overall: {
 current: number;
 total: number;
 percentage: number;
 timeRemaining: string;
 };

 details: {
 currentInvoice: string;
 completed: string[];
 failed: Array<{
 participant: string;
 error: string;
 }>;
 };
 };

 results: {
 title: "Résultat de la génération";

 summary: {
 success: number;
 failed: number;
 totalAmount: number;
 duration: string;
 };

 actions: {
 viewAll: () => void;
 downloadAll: () => void;
 sendAll: () => void;
 retry: (failed: string[]) => void;
 };
 };
 };
}
```

### Section Liste des Factures
```typescript
interface InvoicesList {
 filters: {
 search: {
 placeholder: "N° facture, participant, projet...";
 value: string;
 onChange: (value: string) => void;
 };

 status: {
 label: "Statut";
 options: [
 "Toutes",
 "Brouillon",
 "Envoyée",
 "Payée",
 "En retard",
 "Annulée"
 ];
 value: string[];
 multiSelect: true;
 };

 period: {
 label: "Période";
 type: "date-range";
 value: [Date, Date];
 presets: [
 "Ce mois",
 "Mois dernier",
 "Ce trimestre",
 "Cette année"
 ];
 };

 amount: {
 label: "Montant";
 min: number;
 max: number;
 value: [number, number];
 };

 project: {
 label: "Projet";
 options: Project[];
 value: string[];
 searchable: true;
 };
 };

 table: {
 columns: [
 {
 id: "invoice_number";
 label: "N° Facture";
 sortable: true;
 sticky: true;
 render: (invoice: Invoice) => ({
 number: string;
 type: "standard" | "credit" | "adjustment";
 icon: string;
 });
 },
 {
 id: "participant";
 label: "Participant";
 sortable: true;
 searchable: true;
 render: (participant: Participant) => ({
 name: string;
 email: string;
 type: string;
 });
 },
 {
 id: "project";
 label: "Projet";
 sortable: true;
 filterable: true;
 },
 {
 id: "period";
 label: "Période";
 sortable: true;
 render: (period: Period) => ({
 start: Date;
 end: Date;
 display: string; // "Mars 2024"
 });
 },
 {
 id: "amounts";
 label: "Montants";
 sortable: true;
 render: (amounts: Amounts) => ({
 ht: number;
 tva: number;
 ttc: number;
 currency: "EUR";
 });
 },
 {
 id: "status";
 label: "Statut";
 sortable: true;
 filterable: true;
 render: (status: InvoiceStatus) => ({
 label: string;
 color: string;
 icon: string;
 daysOverdue?: number;
 });
 },
 {
 id: "dates";
 label: "Dates";
 sortable: true;
 render: (dates: InvoiceDates) => ({
 created: Date;
 sent?: Date;
 due: Date;
 paid?: Date;
 });
 },
 {
 id: "actions";
 label: "Actions";
 render: (invoice: Invoice) => {
 const actions = [];

 if (invoice.status === "draft") {
 actions.push(
 { icon: "send", tooltip: "Envoyer", onClick: () => {} },
 { icon: "edit", tooltip: "Modifier", onClick: () => {} }
 );
 }

 if (invoice.status === "sent") {
 actions.push(
 { icon: "payment", tooltip: "Enregistrer paiement", onClick: () => {} },
 { icon: "mail", tooltip: "Renvoyer", onClick: () => {} }
 );
 }

 actions.push(
 { icon: "visibility", tooltip: "Voir", onClick: () => {} },
 { icon: "download", tooltip: "Télécharger", onClick: () => {} },
 { icon: "more_vert", tooltip: "Plus", onClick: () => {} }
 );

 return actions;
 };
 }
 ];

 features: {
 sorting: {
 multiColumn: true;
 defaultSort: { column: "invoice_number", direction: "desc" };
 };

 selection: {
 enabled: true;
 actions: [
 "Envoyer sélection",
 "Télécharger ZIP",
 "Marquer payées",
 "Exporter"
 ];
 };

 pagination: {
 pageSize: 25;
 pageSizeOptions: [10, 25, 50, 100];
 };

 rowActions: {
 quickPayment: boolean;
 quickView: boolean;
 };
 };
 };
}
```

### Section Détail Facture (Modal/Page)
```typescript
interface InvoiceDetail {
 header: {
 invoiceNumber: string;
 status: InvoiceStatus;

 actions: {
 primary: {
 label: string; // Dynamique selon statut
 onClick: () => void;
 };

 secondary: [
 { label: "Télécharger PDF", icon: "download" },
 { label: "Envoyer par email", icon: "mail" },
 { label: "Dupliquer", icon: "copy" },
 { label: "Créer avoir", icon: "receipt" }
 ];
 };
 };

 content: {
 pdf_preview: {
 title: "Aperçu";
 src: string; // URL ou base64
 zoom: number;
 controls: ["zoom_in", "zoom_out", "download", "print"];
 };

 details: {
 title: "Détails de la facture";

 sections: {
 general: {
 invoiceDate: Date;
 dueDate: Date;
 period: string;
 project: string;
 };

 participant: {
 name: string;
 address: string;
 vatNumber?: string;
 customerRef: string;
 };

 lines: Array<{
 description: string;
 quantity: number;
 unit: string;
 unitPrice: number;
 total: number;
 vat: number;
 }>;

 totals: {
 subtotal: number;
 vatAmount: number;
 total: number;
 payments: Payment[];
 balance: number;
 };
 };
 };

 history: {
 title: "Historique";

 timeline: Array<{
 date: Date;
 event: string;
 user?: string;
 details?: string;
 }>;
 };

 payments: {
 title: "Paiements";

 list: Array<{
 date: Date;
 amount: number;
 method: string;
 reference: string;
 status: "completed" | "pending" | "failed";
 }>;

 addPayment: {
 button: "Enregistrer un paiement";
 form: {
 amount: number;
 date: Date;
 method: string;
 reference: string;
 };
 };
 };
 };
}
```

### Section Modèles et Configuration
```typescript
interface InvoiceTemplates {
 title: " Modèles de Factures";

 templates: Array<{
 id: string;
 name: string;
 description: string;
 preview: string; // Thumbnail
 isDefault: boolean;

 customization: {
 logo: boolean;
 colors: boolean;
 fonts: boolean;
 layout: string[];
 };

 actions: {
 preview: () => void;
 setDefault: () => void;
 customize: () => void;
 duplicate: () => void;
 };
 }>;

 settings: {
 numbering: {
 title: "Numérotation";
 format: string; // "FAC-{YYYY}-{MMMM}-{0000}"
 nextNumber: number;
 resetPeriod: "never" | "yearly" | "monthly";
 };

 defaults: {
 paymentTerms: number; // jours
 latePaymentFee: number; // %
 footerText: string;
 legalMentions: string;
 };

 automation: {
 autoSend: boolean;
 sendTime: string; // "HH:mm"
 reminderDelay: number; // jours
 maxReminders: number;
 };
 };
}
```

## État et données

```typescript
interface InvoicesState {
 // Liste des factures
 invoices: {
 list: Invoice[];
 total: number;
 filters: FilterState;
 sorting: SortState;
 };

 // Génération
 generation: {
 wizard: {
 step: number;
 data: GenerationData;
 preview: PreviewData;
 };

 progress: {
 active: boolean;
 current: number;
 total: number;
 errors: GenerationError[];
 };
 };

 // Détail
 detail: {
 invoice: Invoice | null;
 loading: boolean;
 history: HistoryEvent[];
 };

 // Configuration
 config: {
 templates: InvoiceTemplate[];
 settings: InvoiceSettings;
 };
}
```

## Exemple d'implémentation

```tsx
export const InvoicesPage: React.FC = () => {
 const [wizardOpen, setWizardOpen] = useState(false);
 const [selectedInvoices, setSelectedInvoices] = useState<string[]>([]);
 const { invoices, generation, generateInvoices } = useInvoices();

 const handleGenerateInvoices = async (data: GenerationData) => {
 const result = await generateInvoices(data);
 if (result.success) {
 notification.success(`${result.count} factures générées`);
 setWizardOpen(false);
 }
 };

 return (
 <InvoicesLayout>
 <InvoicesHeader
 stats={calculateStats(invoices)}
 onGenerate={() => setWizardOpen(true)}
 />

 <FiltersSection
 filters={filters}
 onChange={setFilters}
 />

 <InvoicesTable
 invoices={invoices}
 onSelect={setSelectedInvoices}
 onAction={handleInvoiceAction}
 />

 <GenerationWizard
 open={wizardOpen}
 onClose={() => setWizardOpen(false)}
 onGenerate={handleGenerateInvoices}
 />

 <InvoiceDetailModal
 invoice={selectedInvoice}
 onClose={() => setSelectedInvoice(null)}
 />
 </InvoicesLayout>
 );
};
```