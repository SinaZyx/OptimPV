# Formulaire Client - Module ERP Client

## Vue d'ensemble

Le formulaire de création et édition client offre une interface intuitive avec autocomplétion d'adresse, validation en temps réel et intégration avec les APIs géographiques pour une saisie rapide et précise des données clients.

## Structure de la page

### Header du Formulaire
```typescript
interface ClientFormHeader {
 title: string; // "Nouveau client" ou "Modifier client - {nom}"

 actions: {
 saveButton: {
 label: "Enregistrer";
 icon: "save";
 variant: "primary";
 onClick: () => void;
 loading: boolean;
 disabled: boolean;
 shortcut: "Ctrl+S";
 };

 saveAndNewButton: {
 label: "Enregistrer et nouveau";
 icon: "add_circle";
 variant: "secondary";
 onClick: () => void;
 visible: boolean; // Mode création uniquement
 };

 cancelButton: {
 label: "Annuler";
 icon: "close";
 onClick: () => void;
 confirmUnsaved: boolean;
 };

 moreActions: {
 icon: "more_vert";
 items: [
 { id: "duplicate", label: "Dupliquer", icon: "content_copy" },
 { id: "template", label: "Sauver comme modèle", icon: "bookmark" },
 { id: "history", label: "Historique", icon: "history" },
 { id: "delete", label: "Supprimer", icon: "delete", danger: true }
 ];
 onAction: (actionId: string) => void;
 };
 };

 status: {
 lastSaved?: Date;
 savingState: "idle" | "saving" | "saved" | "error";
 validationErrors: number;
 completeness: number; // Pourcentage de complétion
 };
}
```

### Section Informations Générales
```typescript
interface GeneralInfoSection {
 title: " Informations générales";
 collapsible: boolean;

 fields: {
 codeClient: {
 label: "Code client";
 type: "text";
 value: string;
 required: true;
 readOnly: boolean; // Auto-généré

 generation: {
 auto: boolean;
 pattern: string; // Ex: "CLI-{YYYY}-{0000}"
 preview: string;
 regenerate: () => void;
 };

 validation: {
 unique: boolean;
 format: RegExp;
 checkUniqueness: (value: string) => Promise<boolean>;
 };
 };

 typeClient: {
 label: "Type de client";
 type: "select";
 value: ClientType;
 required: true;

 options: [
 {
 value: "producteur",
 label: "Producteur",
 icon: "solar_power",
 description: "Client produisant de l'énergie"
 },
 {
 value: "consommateur",
 label: "Consommateur",
 icon: "electric_bolt",
 description: "Client consommant de l'énergie"
 },
 {
 value: "prosumer",
 label: "Prosumer",
 icon: "sync_alt",
 description: "Client producteur et consommateur"
 }
 ];

 onChange: (type: ClientType) => void;
 conditionalFields: Field[]; // Champs affichés selon le type
 };

 nom: {
 label: "Nom / Raison sociale";
 type: "text";
 value: string;
 required: true;
 placeholder: "Entreprise SAS ou Nom Prénom";

 validation: {
 minLength: 2;
 maxLength: 100;
 pattern?: RegExp;
 };

 autocomplete: {
 enabled: boolean;
 source: "database" | "api";
 suggestions: string[];
 };
 };

 status: {
 label: "Statut";
 type: "select";
 value: ClientStatus;
 required: true;

 options: [
 { value: "prospect", label: "Prospect", color: "info" },
 { value: "active", label: "Actif", color: "success" },
 { value: "onboarding", label: "En cours", color: "warning" },
 { value: "suspended", label: "Suspendu", color: "error" },
 { value: "archived", label: "Archivé", color: "grey" }
 ];

 transitions: {
 allowed: Record<ClientStatus, ClientStatus[]>;
 requiresReason: boolean;
 onTransition: (from: ClientStatus, to: ClientStatus) => void;
 };
 };

 tags: {
 label: "Tags";
 type: "multi-select";
 value: string[];

 options: {
 predefined: ["VIP", "Grand compte", "PME", "Résidentiel", "Nouveau"];
 allowCustom: boolean;
 maxTags: 5;
 };

 features: {
 colorCoding: boolean;
 autoSuggest: boolean;
 validation: (tag: string) => boolean;
 };
 };

 description: {
 label: "Description";
 type: "textarea";
 value: string;
 rows: 3;
 maxLength: 500;

 features: {
 richText: boolean;
 characterCount: boolean;
 autoResize: boolean;
 };
 };
 };
}
```

### Section Coordonnées
```typescript
interface ContactSection {
 title: " Coordonnées";

 subsections: {
 contactPrincipal: {
 title: "Contact principal";

 fields: {
 civilite: {
 label: "Civilité";
 type: "radio";
 value: string;
 options: ["M.", "Mme", "Autre"];
 inline: true;
 };

 prenom: {
 label: "Prénom";
 type: "text";
 value: string;
 autocapitalize: "words";
 };

 nom: {
 label: "Nom";
 type: "text";
 value: string;
 autocapitalize: "words";
 required: boolean; // Si différent du nom client
 };

 fonction: {
 label: "Fonction";
 type: "text";
 value: string;
 suggestions: ["Directeur", "Manager", "Technicien", "Comptable"];
 };

 telephone: {
 label: "Téléphone";
 type: "tel";
 value: string;
 required: true;

 formatting: {
 country: "FR";
 format: "+33 X XX XX XX XX";
 validation: RegExp;
 };

 features: {
 multiple: boolean;
 types: ["mobile", "fixe", "fax"];
 preferred: string;
 };
 };

 email: {
 label: "Email";
 type: "email";
 value: string;
 required: true;

 validation: {
 format: RegExp;
 checkMX: boolean; // Vérifier le domaine
 suggestions: string[]; // Correction typos domaines
 };

 features: {
 multiple: boolean;
 verification: {
 enabled: boolean;
 status: "pending" | "verified" | "invalid";
 sendVerification: () => void;
 };
 };
 };
 };
 };

 contactsSecondaires: {
 title: "Contacts secondaires";
 collapsible: true;

 list: {
 items: SecondaryContact[];
 maxItems: 5;

 actions: {
 add: () => void;
 remove: (index: number) => void;
 setPrimary: (index: number) => void;
 };

 template: {
 fields: ["nom", "prenom", "fonction", "telephone", "email"];
 validation: ContactValidation;
 };
 };
 };
 };
}
```

### Section Adresse avec Autocomplétion
```typescript
interface AddressSection {
 title: " Adresse";

 features: {
 autocomplete: {
 enabled: boolean;
 provider: "google" | "here" | "nominatim";

 searchBox: {
 placeholder: "Commencez à taper une adresse...";
 value: string;
 onChange: (value: string) => void;

 suggestions: {
 loading: boolean;
 items: AddressSuggestion[];
 onSelect: (suggestion: AddressSuggestion) => void;

 format: {
 primary: string; // Adresse principale
 secondary: string; // Ville, CP
 icon: "location_on";
 distance?: number; // Si géolocalisation activée
 };
 };

 options: {
 debounceMs: 300;
 minChars: 3;
 maxSuggestions: 5;
 countryRestriction: string[];
 bounds?: GeoBounds; // Limiter à une zone
 types: ["address", "establishment"];
 };
 };
 };

 manualEntry: {
 toggle: {
 label: "Saisie manuelle";
 icon: "edit";
 onClick: () => void;
 };

 fields: {
 numeroRue: {
 label: "N° et voie";
 type: "text";
 value: string;
 required: true;
 placeholder: "123 rue de la Paix";
 };

 complement: {
 label: "Complément";
 type: "text";
 value: string;
 placeholder: "Bâtiment A, Étage 3";
 };

 codePostal: {
 label: "Code postal";
 type: "text";
 value: string;
 required: true;
 pattern: /^\d{5}$/;

 features: {
 autocompleteCity: boolean;
 validation: (cp: string) => Promise<boolean>;
 };
 };

 ville: {
 label: "Ville";
 type: "text";
 value: string;
 required: true;

 suggestions: {
 fromPostalCode: boolean;
 cities: string[];
 };
 };

 pays: {
 label: "Pays";
 type: "select";
 value: string;
 default: "France";

 options: Country[];
 searchable: boolean;
 };
 };
 };

 mapPreview: {
 enabled: boolean;

 component: {
 coordinates: [number, number] | null;
 zoom: number;

 features: {
 marker: {
 draggable: boolean;
 onDragEnd: (coords: [number, number]) => void;
 };

 actions: [
 { icon: "my_location", label: "Centrer", onClick: () => void },
 { icon: "directions", label: "Itinéraire", onClick: () => void },
 { icon: "streetview", label: "Street View", onClick: () => void }
 ];

 validation: {
 checkAddress: boolean;
 confidence: number; // Score de confiance géocodage
 warnings: string[];
 };
 };
 };
 };

 additionalAddresses: {
 title: "Adresses supplémentaires";
 collapsed: true;

 types: [
 { id: "facturation", label: "Adresse de facturation", icon: "receipt" },
 { id: "livraison", label: "Adresse de livraison", icon: "local_shipping" },
 { id: "technique", label: "Adresse technique", icon: "engineering" }
 ];

 addresses: AdditionalAddress[];

 actions: {
 add: (type: string) => void;
 copyFrom: (source: "principale" | string) => void;
 remove: (id: string) => void;
 };
 };
 };
}
```

### Section Informations Commerciales
```typescript
interface CommercialInfoSection {
 title: " Informations commerciales";
 collapsible: true;
 visible: boolean; // Selon permissions

 fields: {
 commercial: {
 label: "Commercial assigné";
 type: "select";
 value: string;

 options: {
 users: User[];
 showAvatar: boolean;
 showRole: boolean;
 groupBy: "team" | "region";
 };

 features: {
 history: Assignment[];
 reassign: {
 enabled: boolean;
 requireReason: boolean;
 notifyPrevious: boolean;
 };
 };
 };

 origine: {
 label: "Origine du contact";
 type: "select";
 value: string;

 options: [
 "Site web",
 "Recommandation",
 "Salon",
 "Cold calling",
 "Publicité",
 "Partenaire",
 "Autre"
 ];

 conditionalField: {
 when: "Autre";
 show: { field: "origineDetails", type: "text" };
 };
 };

 potentiel: {
 label: "Potentiel commercial";
 type: "range";
 value: number;
 min: 1;
 max: 5;

 display: {
 type: "stars" | "slider" | "select";
 labels: ["Faible", "Moyen", "Bon", "Très bon", "Excellent"];
 colors: ["#f44336", "#ff9800", "#ffeb3b", "#8bc34a", "#4caf50"];
 };
 };

 notes: {
 label: "Notes commerciales";
 type: "rich-text";
 value: string;

 features: {
 templates: NoteTemplate[];
 mentions: boolean; // @user
 tasks: boolean; // Créer des tâches depuis les notes
 history: NoteHistory[];
 };
 };
 };
}
```

### Section Paramètres Techniques
```typescript
interface TechnicalParamsSection {
 title: " Paramètres techniques";
 collapsible: true;

 subsections: {
 production: {
 title: "Production solaire";
 visible: boolean; // Si type = producteur ou prosumer

 fields: {
 puissanceInstallee: {
 label: "Puissance installée";
 type: "number";
 value: number;
 unit: "kWc";
 min: 0;
 step: 0.1;

 calculator: {
 enabled: boolean;
 fromPanels: (panels: Panel[]) => number;
 };
 };

 typeInstallation: {
 label: "Type d'installation";
 type: "select";
 value: string;

 options: [
 "Toiture résidentielle",
 "Toiture industrielle",
 "Ombrière",
 "Au sol",
 "Façade"
 ];

 impact: {
 onTariff: boolean;
 onProduction: boolean;
 };
 };

 dateRaccordement: {
 label: "Date de raccordement";
 type: "date";
 value: Date;
 max: "today";

 relatedFields: {
 contratAchat: boolean;
 tarif: boolean;
 };
 };

 productionAnnuelle: {
 label: "Production annuelle estimée";
 type: "number";
 value: number;
 unit: "kWh/an";

 calculation: {
 auto: boolean;
 factors: ["puissance", "localisation", "orientation"];
 override: boolean;
 };
 };
 };
 };

 consommation: {
 title: "Consommation";
 visible: boolean; // Si type = consommateur ou prosumer

 fields: {
 consommationAnnuelle: {
 label: "Consommation annuelle";
 type: "number";
 value: number;
 unit: "kWh/an";

 estimation: {
 fromHistorique: boolean;
 fromProfile: boolean;
 lastUpdate: Date;
 };
 };

 profilConsommation: {
 label: "Profil de consommation";
 type: "select";
 value: string;

 options: [
 "Résidentiel standard",
 "Résidentiel chauffage électrique",
 "Tertiaire bureaux",
 "Commerce",
 "Industrie",
 "Agriculture"
 ];

 curves: {
 preview: boolean;
 customize: boolean;
 };
 };

 compteur: {
 label: "Référence compteur";
 type: "text";
 value: string;

 features: {
 validation: boolean;
 linkToEnedis: boolean;
 telerelevé: boolean;
 };
 };
 };
 };

 stockage: {
 title: "Stockage";
 collapsible: true;
 optional: true;

 enabled: boolean;

 fields: {
 capaciteBatterie: {
 label: "Capacité batterie";
 type: "number";
 value: number;
 unit: "kWh";
 min: 0;
 step: 0.5;
 };

 technologie: {
 label: "Technologie";
 type: "select";
 value: string;
 options: ["Lithium-ion", "LFP", "Plomb", "Autre"];
 };

 dateMiseEnService: {
 label: "Date mise en service";
 type: "date";
 value: Date;
 };
 };
 };
 };
}
```

### Section Documents
```typescript
interface DocumentsSection {
 title: " Documents";
 collapsible: true;

 categories: [
 {
 id: "administratif";
 label: "Administratif";
 icon: "folder";
 count: number;

 documentTypes: [
 "KBis",
 "RIB",
 "Attestation assurance",
 "Procuration"
 ];
 },
 {
 id: "technique";
 label: "Technique";
 icon: "engineering";
 count: number;

 documentTypes: [
 "Plan installation",
 "Fiche technique",
 "Contrat maintenance",
 "Certificat conformité"
 ];
 },
 {
 id: "commercial";
 label: "Commercial";
 icon: "business_center";
 count: number;

 documentTypes: [
 "Devis",
 "Contrat",
 "Facture",
 "Bon de commande"
 ];
 }
 ];

 uploader: {
 accept: string[]; // Types de fichiers acceptés
 maxSize: number; // En MB
 multiple: boolean;

 dragDrop: {
 enabled: boolean;
 zone: HTMLElement;
 message: string;
 };

 onUpload: (files: File[]) => void;
 onProgress: (progress: number) => void;
 onComplete: (documents: Document[]) => void;
 };

 documentList: {
 documents: Document[];

 features: {
 preview: boolean;
 download: boolean;
 share: boolean;
 version: boolean;
 ocr: boolean; // Reconnaissance de texte
 };

 actions: {
 view: (doc: Document) => void;
 download: (doc: Document) => void;
 delete: (doc: Document) => void;
 rename: (doc: Document) => void;
 tag: (doc: Document, tags: string[]) => void;
 };
 };
}
```

## État et données

```typescript
interface ClientFormState {
 // Mode
 mode: "create" | "edit";
 clientId?: string;

 // Données formulaire
 formData: {
 general: GeneralInfo;
 contact: ContactInfo;
 address: AddressInfo;
 commercial: CommercialInfo;
 technical: TechnicalInfo;
 documents: Document[];
 };

 // Validation
 validation: {
 errors: Record<string, ValidationError>;
 warnings: Record<string, string>;
 touched: Record<string, boolean>;
 isValid: boolean;
 };

 // État UI
 ui: {
 loading: boolean;
 saving: boolean;
 sections: {
 expanded: string[];
 visible: string[];
 };
 addressAutocomplete: {
 suggestions: AddressSuggestion[];
 loading: boolean;
 selected?: AddressSuggestion;
 };
 };

 // Métadonnées
 metadata: {
 createdAt?: Date;
 createdBy?: string;
 updatedAt?: Date;
 updatedBy?: string;
 version: number;
 };

 // État temporaire
 draft: {
 isDirty: boolean;
 lastAutoSave?: Date;
 restoreAvailable: boolean;
 };
}
```

## API Endpoints

```typescript
// CRUD Client
POST /api/clients
PUT /api/clients/:id
GET /api/clients/:id
DELETE /api/clients/:id

// Validation
POST /api/clients/validate
Body: {
 field: string;
 value: any;
 context: Record<string, any>;
}

// Autocomplétion adresse
GET /api/geocoding/autocomplete
Query: {
 q: string;
 limit: number;
 bounds?: string;
 country?: string;
}

// Géocodage
POST /api/geocoding/geocode
Body: {
 address: string;
 components?: AddressComponents;
}

// Upload documents
POST /api/clients/:id/documents
Content-Type: multipart/form-data

// Génération code client
GET /api/clients/generate-code
Query: {
 pattern?: string;
 type?: string;
}
```

## Exemple d'implémentation

```tsx
export const ClientForm: React.FC<ClientFormProps> = ({ mode, clientId }) => {
 const [formData, setFormData] = useState<FormData>(initialFormData);
 const [validation, setValidation] = useState<ValidationState>({});
 const { addressSuggestions, searchAddress } = useAddressAutocomplete();

 // Auto-save draft
 useEffect(() => {
 const autoSave = debounce(() => {
 if (formData.isDirty) {
 saveDraft(formData);
 }
 }, 5000);

 autoSave();
 return () => autoSave.cancel();
 }, [formData]);

 // Validation temps réel
 const validateField = useCallback(async (field: string, value: any) => {
 const error = await validateClientField(field, value, formData);
 setValidation(prev => ({
...prev,
 errors: {...prev.errors, [field]: error }
 }));
 }, [formData]);

 const handleSubmit = async () => {
 const isValid = await validateForm(formData);
 if (!isValid) return;

 try {
 const client = mode === "create"
? await createClient(formData)
: await updateClient(clientId, formData);

 showNotification("Client enregistré avec succès", "success");
 navigate(`/clients/${client.id}`);
 } catch (error) {
 showNotification("Erreur lors de l'enregistrement", "error");
 }
 };

 return (
 <FormLayout>
 <ClientFormHeader
 mode={mode}
 onSave={handleSubmit}
 onCancel={() => navigate("/clients")}
 validation={validation}
 />

 <FormSections>
 <GeneralInfoSection
 data={formData.general}
 onChange={(data) => updateFormData("general", data)}
 errors={validation.errors}
 />

 <ContactSection
 data={formData.contact}
 onChange={(data) => updateFormData("contact", data)}
 errors={validation.errors}
 />

 <AddressSection
 data={formData.address}
 onChange={(data) => updateFormData("address", data)}
 suggestions={addressSuggestions}
 onSearch={searchAddress}
 errors={validation.errors}
 />

 {hasPermission("commercial") && (
 <CommercialInfoSection
 data={formData.commercial}
 onChange={(data) => updateFormData("commercial", data)}
 />
 )}

 <TechnicalParamsSection
 data={formData.technical}
 clientType={formData.general.typeClient}
 onChange={(data) => updateFormData("technical", data)}
 />

 <DocumentsSection
 documents={formData.documents}
 onUpload={handleDocumentUpload}
 onDelete={handleDocumentDelete}
 />
 </FormSections>
 </FormLayout>
 );
};
```