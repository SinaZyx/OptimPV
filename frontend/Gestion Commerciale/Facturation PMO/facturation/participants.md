# Page Gestion des Participants - Module Facturation

## Vue d'ensemble

La page Gestion des Participants permet de gérer les membres d'un projet d'autoconsommation collective, leurs allocations et leurs informations de facturation.

## Structure de la page

### Header Principal
```typescript
interface ParticipantsHeader {
 title: " Gestion des Participants";
 projectName: string;

 stats: {
 totalParticipants: number;
 activeParticipants: number;
 totalAllocation: number; // %
 monthlyVolume: number; // kWh
 };

 actions: {
 addParticipant: {
 label: " Ajouter un participant";
 onClick: () => void;
 variant: "primary";
 };

 importBatch: {
 label: " Import en masse";
 accept: [".csv", ".xlsx"];
 onImport: (file: File) => void;
 };

 exportList: {
 label: " Exporter";
 formats: ["Excel", "CSV", "PDF"];
 onClick: (format: string) => void;
 };
 };
}
```

### Section Liste des Participants
```typescript
interface ParticipantsList {
 viewMode: "table" | "cards" | "allocation";

 filters: {
 search: {
 placeholder: "Rechercher par nom, email, référence...";
 value: string;
 onChange: (value: string) => void;
 };

 type: {
 label: "Type";
 options: ["Tous", "Producteur", "Consommateur", "Prosumer"];
 value: string;
 };

 status: {
 label: "Statut";
 options: ["Tous", "Actif", "Suspendu", "En attente"];
 value: string;
 };

 allocation: {
 label: "Allocation";
 options: ["Tous", "Avec allocation", "Sans allocation"];
 value: string;
 };
 };

 tableView: {
 columns: [
 {
 id: "participant";
 label: "Participant";
 sortable: true;
 render: (participant: Participant) => ({
 name: string;
 email: string;
 avatar: string;
 type: "producer" | "consumer" | "prosumer";
 });
 },
 {
 id: "allocation";
 label: "Allocation";
 sortable: true;
 editable: true;
 render: (value: number) => ({
 percentage: number;
 volume: number; // kWh estimé
 editMode: "inline" | "modal";
 });
 },
 {
 id: "consumption";
 label: "Consommation";
 sortable: true;
 render: () => ({
 monthly: number;
 trend: "up" | "down" | "stable";
 sparkline: number[];
 });
 },
 {
 id: "billing";
 label: "Facturation";
 render: () => ({
 lastInvoice: Date;
 amount: number;
 status: "paid" | "pending" | "overdue";
 });
 },
 {
 id: "status";
 label: "Statut";
 sortable: true;
 render: (status: string) => ({
 label: string;
 color: "success" | "warning" | "error";
 since: Date;
 });
 },
 {
 id: "actions";
 label: "Actions";
 render: () => [
 { icon: "edit", tooltip: "Éditer" },
 { icon: "receipt", tooltip: "Factures" },
 { icon: "pause", tooltip: "Suspendre" },
 { icon: "delete", tooltip: "Supprimer" }
 ];
 }
 ];

 bulkActions: {
 visible: boolean;
 actions: [
 "Modifier allocations",
 "Générer factures",
 "Envoyer rappels",
 "Exporter sélection"
 ];
 };
 };

 allocationView: {
 visualization: {
 type: "sunburst" | "treemap" | "pie";
 interactive: true;

 data: {
 total: number; // kWh à répartir
 allocated: number; // kWh alloués
 participants: Array<{
 id: string;
 name: string;
 type: string;
 allocation: number; // %
 volume: number; // kWh
 color: string;
 }>;
 };

 controls: {
 dragToAdjust: boolean;
 showVolumes: boolean;
 lockAllocations: string[]; // IDs verrouillés
 };
 };

 quickBalance: {
 unallocated: number; // %
 autoBalance: () => void;
 validate: () => ValidationResult;
 };
 };
}
```

### Section Formulaire Participant
```typescript
interface ParticipantForm {
 mode: "create" | "edit";

 sections: {
 identification: {
 title: "Identification";
 fields: {
 type: {
 label: "Type de participant";
 type: "radio";
 options: [
 { value: "consumer", label: "Consommateur", icon: "power" },
 { value: "producer", label: "Producteur", icon: "solar_power" },
 { value: "prosumer", label: "Prosumer", icon: "sync_alt" }
 ];
 required: true;
 };

 name: {
 label: "Nom/Raison sociale";
 type: "text";
 required: true;
 validation: "min:3,max:100";
 };

 reference: {
 label: "Référence interne";
 type: "text";
 placeholder: "Auto-généré si vide";
 unique: true;
 };

 email: {
 label: "Email de contact";
 type: "email";
 required: true;
 validation: "email";
 };
 };
 };

 billing: {
 title: "Informations de Facturation";
 fields: {
 billingAddress: {
 label: "Adresse de facturation";
 type: "address";
 required: true;
 copyFromMain: boolean;
 };

 vatNumber: {
 label: "Numéro TVA";
 type: "text";
 validation: "vat";
 conditional: "if business";
 };

 paymentMethod: {
 label: "Mode de paiement";
 type: "select";
 options: ["Prélèvement", "Virement", "Chèque", "CB"];
 required: true;
 };

 iban: {
 label: "IBAN";
 type: "iban";
 conditional: "if prélèvement";
 validation: "iban";
 };
 };
 };

 technical: {
 title: "Données Techniques";
 fields: {
 meteringPoint: {
 label: "Point de comptage";
 type: "text";
 placeholder: "PDL/PRM";
 validation: "pdl";
 };

 contractPower: {
 label: "Puissance souscrite (kVA)";
 type: "number";
 min: 3;
 max: 36;
 step: 3;
 };

 estimatedConsumption: {
 label: "Consommation annuelle estimée (kWh)";
 type: "number";
 min: 0;
 help: "Basé sur historique ou estimation";
 };

 productionCapacity: {
 label: "Capacité de production (kWc)";
 type: "number";
 min: 0;
 conditional: "if producer or prosumer";
 };
 };
 };

 allocation: {
 title: "Allocation Initiale";
 fields: {
 allocationPercentage: {
 label: "Part d'allocation (%)";
 type: "slider";
 min: 0;
 max: 100;
 step: 0.1;
 value: number;

 preview: {
 monthlyVolume: number; // kWh estimés
 monthlyValue: number; // € estimés
 };
 };

 allocationRules: {
 label: "Règles d'allocation";
 type: "select";
 options: [
 "Fixe toute l'année",
 "Variable par saison",
 "Dynamique selon production",
 "Personnalisé"
 ];
 };

 priorityLevel: {
 label: "Niveau de priorité";
 type: "number";
 min: 1;
 max: 10;
 help: "1 = priorité maximale";
 };
 };
 };
 };

 validation: {
 onSubmit: () => ValidationResult;
 showErrors: boolean;
 autoSave: boolean;
 };
}
```

### Section Analytics Participants
```typescript
interface ParticipantAnalytics {
 title: " Analytics Participants";

 metrics: {
 distribution: {
 title: "Répartition par Type";
 chart: {
 type: "donut";
 data: {
 consumers: number;
 producers: number;
 prosumers: number;
 };
 };
 };

 consumptionTrends: {
 title: "Tendances de Consommation";
 chart: {
 type: "area";
 period: "12 months";
 series: [
 { name: "Consommation totale", data: number[] },
 { name: "Production totale", data: number[] },
 { name: "Autoconsommation", data: number[] }
 ];
 };
 };

 topParticipants: {
 title: "Top Participants";
 tabs: ["Consommation", "Production", "Facturation"];

 list: Array<{
 rank: number;
 participant: string;
 value: number;
 unit: string;
 change: number; // % vs période précédente
 }>;
 };

 allocationEfficiency: {
 title: "Efficacité des Allocations";

 metrics: {
 utilizationRate: number; // % allocation utilisée
 mismatchRate: number; // % sur/sous-allocation
 reallocationFrequency: number; // Nb ajustements/mois
 };

 recommendations: string[];
 };
 };
}
```

### Section Historique et Actions
```typescript
interface ParticipantHistory {
 participant: string;

 timeline: {
 events: Array<{
 date: Date;
 type: "creation" | "modification" | "allocation_change" | "status_change" | "billing";
 description: string;
 user: string;
 details?: any;
 }>;

 filters: {
 type: string[];
 dateRange: [Date, Date];
 };
 };

 documents: {
 title: "Documents";
 items: Array<{
 id: string;
 type: "contract" | "invoice" | "report" | "other";
 name: string;
 date: Date;
 size: string;
 actions: ["view", "download", "delete"];
 }>;

 upload: {
 accept: string[];
 maxSize: number; // MB
 onUpload: (file: File) => void;
 };
 };
}
```

## État et données

```typescript
interface ParticipantsState {
 // Liste des participants
 participants: {
 list: Participant[];
 total: number;
 loading: boolean;
 filters: FilterState;
 };

 // Allocations
 allocations: {
 total: number; // kWh à répartir
 allocated: number; // kWh alloués
 rules: AllocationRule[];
 lastUpdate: Date;
 };

 // Formulaire
 form: {
 mode: "create" | "edit";
 data: Partial<Participant>;
 errors: ValidationError[];
 isDirty: boolean;
 };

 // UI
 ui: {
 viewMode: "table" | "cards" | "allocation";
 selectedParticipants: string[];
 expandedRows: string[];
 activeModal: string | null;
 };
}
```

## Exemple d'implémentation

```tsx
export const ParticipantsPage: React.FC = () => {
 const [viewMode, setViewMode] = useState<ViewMode>("table");
 const [selectedParticipants, setSelectedParticipants] = useState<string[]>([]);
 const { participants, allocations, loading } = useParticipants();

 const handleAllocationChange = (participantId: string, newValue: number) => {
 updateAllocation(participantId, newValue);
 // Recalculer automatiquement les autres si nécessaire
 };

 return (
 <ParticipantsLayout>
 <ParticipantsHeader
 stats={calculateStats(participants)}
 onAddParticipant={() => openModal("create")}
 />

 <ViewModeToggle
 value={viewMode}
 onChange={setViewMode}
 />

 {viewMode === "table" && (
 <ParticipantsTable
 data={participants}
 onSelect={setSelectedParticipants}
 onAllocationChange={handleAllocationChange}
 />
 )}

 {viewMode === "allocation" && (
 <AllocationVisualizer
 participants={participants}
 allocations={allocations}
 onAdjust={handleAllocationChange}
 />
 )}

 <ParticipantAnalytics
 participants={participants}
 period="last-12-months"
 />

 <ParticipantFormModal
 open={modalOpen}
 mode={formMode}
 onClose={() => setModalOpen(false)}
 onSave={handleSaveParticipant}
 />
 </ParticipantsLayout>
 );
};
```