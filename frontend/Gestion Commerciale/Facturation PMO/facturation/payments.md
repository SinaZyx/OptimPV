# Page Gestion des Paiements - Module Facturation

## Vue d'ensemble

La page Paiements permet de gérer l'ensemble des encaissements, suivre les impayés et automatiser les relances pour les projets d'autoconsommation collective.

## Structure de la page

### Header Principal
```typescript
interface PaymentsHeader {
 title: " Gestion des Paiements";

 metrics: {
 awaiting: {
 label: "En attente";
 value: number;
 format: "currency";
 icon: "pending";
 color: "warning";
 };

 collected: {
 label: "Encaissé ce mois";
 value: number;
 format: "currency";
 icon: "check_circle";
 color: "success";
 };

 overdue: {
 label: "En retard";
 value: number;
 format: "currency";
 icon: "warning";
 color: "error";
 details: string; // "X factures"
 };

 collectionRate: {
 label: "Taux de recouvrement";
 value: number;
 format: "percentage";
 icon: "analytics";
 trend: "up" | "down" | "stable";
 };
 };

 actions: {
 importPayments: {
 label: " Import bancaire";
 onClick: () => void;
 variant: "primary";
 };

 sendReminders: {
 label: " Envoyer relances";
 onClick: () => void;
 badge?: number; // Nombre de relances à envoyer
 };

 reconciliation: {
 label: " Rapprochement";
 onClick: () => void;
 };
 };
}
```

### Section Import Bancaire
```typescript
interface BankImport {
 modal: {
 title: "Import de Relevé Bancaire";

 steps: [
 {
 id: "upload";
 title: "Chargement du fichier";

 content: {
 dropZone: {
 accept: [".ofx", ".csv", ".xls", ".xlsx"];
 maxSize: 10; // MB

 formats: {
 supported: [
 { format: "OFX", description: "Format bancaire standard" },
 { format: "CSV", description: "Export Excel banque" },
 { format: "CFONB", description: "Format interbancaire" }
 ];

 bankTemplates: [
 "Crédit Agricole",
 "BNP Paribas",
 "Société Générale",
 "LCL",
 "Autre"
 ];
 };
 };

 manualConfig: {
 visible: boolean; // Si format non reconnu

 fields: {
 dateColumn: number;
 amountColumn: number;
 referenceColumn: number;
 descriptionColumn: number;
 delimiter: string;
 dateFormat: string;
 decimalSeparator: string;
 };
 };
 };
 },
 {
 id: "mapping";
 title: "Correspondance des paiements";

 content: {
 autoMatch: {
 status: "processing" | "complete";
 stats: {
 total: number;
 matched: number;
 uncertain: number;
 unmatched: number;
 };

 criteria: [
 "Montant exact",
 "Référence facture",
 "Nom participant",
 "Date proche"
 ];
 };

 matchingTable: {
 columns: [
 "Date",
 "Montant",
 "Libellé bancaire",
 "Facture suggérée",
 "Confiance",
 "Action"
 ];

 rows: Array<{
 bankTransaction: {
 date: Date;
 amount: number;
 reference: string;
 description: string;
 };

 suggestion: {
 invoice: Invoice | null;
 confidence: number; // 0-100%
 matchReasons: string[];
 alternatives: Invoice[];
 };

 action: "auto" | "manual" | "ignore";
 }>;

 bulkActions: {
 acceptAllSuggestions: () => void;
 ignoreUnmatched: () => void;
 };
 };
 };
 },
 {
 id: "validation";
 title: "Validation et import";

 content: {
 summary: {
 toImport: number;
 totalAmount: number;

 breakdown: {
 automatic: { count: number; amount: number };
 manual: { count: number; amount: number };
 ignored: { count: number; amount: number };
 };

 impacts: {
 invoicesToUpdate: number;
 newFullyPaid: number;
 remainingOverdue: number;
 };
 };

 preview: {
 changes: Array<{
 invoice: string;
 before: PaymentStatus;
 after: PaymentStatus;
 payment: number;
 }>;
 };

 importOptions: {
 sendConfirmations: boolean;
 updateAccountingExport: boolean;
 generateReport: boolean;
 };
 };
 }
 ];
 };
}
```

### Section Liste des Paiements
```typescript
interface PaymentsList {
 views: {
 tabs: [
 {
 id: "all";
 label: "Tous les paiements";
 count?: number;
 },
 {
 id: "pending";
 label: "En attente";
 count: number;
 color: "warning";
 },
 {
 id: "overdue";
 label: "En retard";
 count: number;
 color: "error";
 },
 {
 id: "recent";
 label: "Récents";
 badge: "new";
 }
 ];

 activeView: string;
 };

 filters: {
 dateRange: {
 label: "Période";
 value: [Date, Date];
 presets: ["Cette semaine", "Ce mois", "30 derniers jours"];
 };

 status: {
 label: "Statut";
 options: [
 { value: "paid", label: "Payé", color: "success" },
 { value: "partial", label: "Partiel", color: "info" },
 { value: "pending", label: "En attente", color: "warning" },
 { value: "overdue", label: "En retard", color: "error" }
 ];
 multiSelect: true;
 };

 project: {
 label: "Projet";
 options: Project[];
 searchable: true;
 };

 amountRange: {
 label: "Montant";
 min: number;
 max: number;
 value: [number, number];
 };
 };

 table: {
 columns: [
 {
 id: "invoice";
 label: "Facture";
 render: (invoice: Invoice) => ({
 number: string;
 participant: string;
 project: string;
 link: () => void;
 });
 },
 {
 id: "amounts";
 label: "Montants";
 render: (payment: Payment) => ({
 total: number;
 paid: number;
 remaining: number;
 percentage: number;
 });
 },
 {
 id: "dates";
 label: "Dates";
 render: (dates: PaymentDates) => ({
 due: Date;
 lastPayment?: Date;
 daysOverdue?: number;
 });
 },
 {
 id: "status";
 label: "Statut";
 render: (status: PaymentStatus) => ({
 label: string;
 color: string;
 icon: string;
 progress: number;
 });
 },
 {
 id: "payments";
 label: "Paiements";
 render: (payments: PaymentHistory[]) => ({
 count: number;
 list: Array<{
 date: Date;
 amount: number;
 method: string;
 }>;
 expandable: true;
 });
 },
 {
 id: "reminders";
 label: "Relances";
 render: (reminders: Reminder[]) => ({
 sent: number;
 lastDate?: Date;
 nextDate?: Date;
 status: "scheduled" | "sent" | "none";
 });
 },
 {
 id: "actions";
 label: "Actions";
 render: (payment: Payment) => [
 {
 icon: "payment",
 tooltip: "Enregistrer paiement",
 onClick: () => {},
 visible: payment.status!== "paid"
 },
 {
 icon: "mail",
 tooltip: "Envoyer relance",
 onClick: () => {},
 visible: payment.status === "overdue"
 },
 {
 icon: "history",
 tooltip: "Historique",
 onClick: () => {}
 }
 ];
 }
 ];

 features: {
 expandableRows: {
 enabled: true;
 content: "payment-history";
 };

 sorting: {
 defaultSort: { column: "dates.due", direction: "asc" };
 };

 bulkActions: {
 visible: boolean;
 actions: [
 "Envoyer relances",
 "Marquer comme payé",
 "Exporter sélection",
 "Générer rapport"
 ];
 };
 };
 };
}
```

### Section Relances Automatiques
```typescript
interface RemindersManagement {
 title: " Gestion des Relances";

 configuration: {
 rules: Array<{
 id: string;
 name: string;
 active: boolean;

 trigger: {
 type: "days_overdue" | "amount_threshold" | "custom";
 value: number;
 condition?: string;
 };

 template: {
 subject: string;
 content: string; // Avec variables
 attachments: ["invoice", "payment_history"];
 };

 schedule: {
 frequency: "once" | "weekly" | "monthly";
 maxReminders: number;
 escalation: boolean;
 };

 actions: {
 edit: () => void;
 test: () => void;
 viewHistory: () => void;
 };
 }>;

 addRule: {
 button: "Ajouter une règle";
 wizard: boolean;
 };
 };

 preview: {
 title: "Relances à envoyer";

 list: Array<{
 participant: string;
 invoice: string;
 daysOverdue: number;
 amount: number;
 reminderNumber: number;
 template: string;

 actions: {
 preview: () => void;
 exclude: () => void;
 sendNow: () => void;
 };
 }>;

 bulkActions: {
 sendAll: {
 label: "Envoyer toutes les relances";
 count: number;
 onClick: () => void;
 };

 schedule: {
 label: "Programmer envoi";
 datetime: Date;
 onClick: () => void;
 };
 };
 };

 history: {
 title: "Historique des relances";

 stats: {
 sent: number;
 effectiveness: number; // % payé après relance
 averageDelay: number; // Jours avant paiement
 };

 log: Array<{
 date: Date;
 participant: string;
 invoice: string;
 reminderNumber: number;
 result: "sent" | "failed" | "bounced";
 paymentReceived?: Date;
 }>;
 };
}
```

### Section Tableau de Bord Paiements
```typescript
interface PaymentsDashboard {
 title: " Tableau de Bord Paiements";

 charts: {
 collectionEvolution: {
 title: "Évolution des Encaissements";
 type: "area";
 period: "12 months";

 series: [
 { name: "Facturé", data: number[] },
 { name: "Encaissé", data: number[] },
 { name: "En attente", data: number[] }
 ];

 annotations: {
 average: number;
 trend: "improving" | "degrading" | "stable";
 };
 };

 agingBalance: {
 title: "Balance Âgée";
 type: "horizontal-bar";

 categories: [
 "Non échu",
 "0-30 jours",
 "31-60 jours",
 "61-90 jours",
 ">90 jours"
 ];

 data: {
 amounts: number[];
 counts: number[]; // Nombre de factures
 colors: string[];
 };

 actions: {
 drillDown: (category: string) => void;
 };
 };

 paymentMethods: {
 title: "Modes de Paiement";
 type: "donut";

 data: [
 { method: "Prélèvement", amount: number, percentage: number },
 { method: "Virement", amount: number, percentage: number },
 { method: "CB", amount: number, percentage: number },
 { method: "Chèque", amount: number, percentage: number }
 ];
 };

 participantRanking: {
 title: "Fiabilité Participants";
 type: "table";

 metrics: [
 "Paiements à temps",
 "Retard moyen",
 "Montant impayé",
 "Score fiabilité"
 ];

 data: Array<{
 participant: string;
 onTime: number; // %
 avgDelay: number; // jours
 unpaid: number; // €
 score: number; // 0-100
 trend: "up" | "down" | "stable";
 }>;
 };
 };
}
```

### Section Enregistrement Manuel
```typescript
interface ManualPaymentEntry {
 modal: {
 title: "Enregistrer un Paiement";

 form: {
 invoice: {
 label: "Facture";
 type: "select";
 options: Invoice[];
 searchable: true;
 required: true;

 info: {
 participant: string;
 amount: number;
 balance: number;
 };
 };

 payment: {
 amount: {
 label: "Montant";
 type: "currency";
 max: number; // Balance due
 required: true;
 };

 date: {
 label: "Date du paiement";
 type: "date";
 max: Date; // Today
 required: true;
 };

 method: {
 label: "Mode de paiement";
 type: "select";
 options: ["Virement", "Chèque", "CB", "Espèces", "Autre"];
 required: true;
 };

 reference: {
 label: "Référence";
 type: "text";
 placeholder: "N° chèque, référence virement...";
 };

 notes: {
 label: "Notes";
 type: "textarea";
 maxLength: 500;
 };
 };

 options: {
 sendConfirmation: {
 label: "Envoyer confirmation au participant";
 type: "checkbox";
 default: true;
 };

 closeInvoice: {
 label: "Clôturer la facture si soldée";
 type: "checkbox";
 default: true;
 };
 };
 };

 validation: {
 showBalance: boolean;
 warnings: string[];

 summary: {
 before: { balance: number; status: string };
 after: { balance: number; status: string };
 };
 };
 };
}
```

## État et données

```typescript
interface PaymentsState {
 // Dashboard
 dashboard: {
 metrics: PaymentMetrics;
 charts: ChartData[];
 period: DateRange;
 };

 // Liste paiements
 payments: {
 list: Payment[];
 filters: FilterState;
 view: "all" | "pending" | "overdue" | "recent";
 selected: string[];
 };

 // Import bancaire
 bankImport: {
 step: number;
 file: File | null;
 transactions: BankTransaction[];
 mappings: PaymentMapping[];
 status: ImportStatus;
 };

 // Relances
 reminders: {
 rules: ReminderRule[];
 pending: PendingReminder[];
 history: ReminderHistory[];
 };

 // UI
 ui: {
 activeModal: string | null;
 loading: Record<string, boolean>;
 errors: Record<string, Error>;
 };
}
```

## Exemple d'implémentation

```tsx
export const PaymentsPage: React.FC = () => {
 const [view, setView] = useState<PaymentView>("pending");
 const [importModalOpen, setImportModalOpen] = useState(false);
 const { payments, metrics, importBankFile, sendReminders } = usePayments();

 const handleBankImport = async (file: File, mappings: PaymentMapping[]) => {
 const result = await importBankFile(file, mappings);
 if (result.success) {
 notification.success(`${result.imported} paiements importés`);
 setImportModalOpen(false);
 refreshPayments();
 }
 };

 return (
 <PaymentsLayout>
 <PaymentsHeader
 metrics={metrics}
 onImport={() => setImportModalOpen(true)}
 onSendReminders={handleSendReminders}
 />

 <Tabs value={view} onChange={setView}>
 <Tab value="all" label="Tous" />
 <Tab value="pending" label="En attente" badge={metrics.pending} />
 <Tab value="overdue" label="En retard" badge={metrics.overdue} color="error" />
 <Tab value="recent" label="Récents" />
 </Tabs>

 <PaymentsTable
 payments={filterByView(payments, view)}
 onPaymentEntry={handlePaymentEntry}
 onSendReminder={handleSendReminder}
 />

 <PaymentsDashboard
 period="last-12-months"
 onDrillDown={handleDrillDown}
 />

 <BankImportModal
 open={importModalOpen}
 onClose={() => setImportModalOpen(false)}
 onImport={handleBankImport}
 />

 <RemindersConfiguration
 rules={reminderRules}
 onUpdateRules={updateReminderRules}
 />
 </PaymentsLayout>
 );
};
```