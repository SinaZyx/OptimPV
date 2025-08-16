# Page Configuration Sécurité - Module Security

## Vue d'ensemble

La page Configuration Sécurité permet de gérer les paramètres de sécurité de l'application, les accès utilisateurs, et les configurations sensibles.

## Structure de la page

### Header Principal
```typescript
interface SecurityConfigHeader {
 title: " Configuration Sécurité";
 subtitle: "Gestion des accès et paramètres de sécurité";

 badges: [
 {
 label: "Dernière mise à jour";
 value: Date;
 icon: "update";
 },
 {
 label: "Niveau sécurité";
 value: "Élevé" | "Moyen" | "Faible";
 color: "success" | "warning" | "error";
 icon: "shield";
 }
 ];

 actions: {
 auditButton: {
 label: " Audit Sécurité";
 onClick: () => void;
 tooltip: "Lancer un audit complet";
 };

 backupButton: {
 label: " Sauvegarder";
 onClick: () => void;
 loading: boolean;
 };
 };
}
```

### Section Authentification
```typescript
interface AuthenticationSection {
 title: " Authentification";

 passwordPolicy: {
 title: "Politique de mots de passe";
 settings: {
 minLength: {
 label: "Longueur minimale";
 value: number; // 8-32
 type: "slider";
 onChange: (value: number) => void;
 };

 requireUppercase: {
 label: "Majuscules obligatoires";
 value: boolean;
 type: "switch";
 };

 requireLowercase: {
 label: "Minuscules obligatoires";
 value: boolean;
 type: "switch";
 };

 requireNumbers: {
 label: "Chiffres obligatoires";
 value: boolean;
 type: "switch";
 };

 requireSpecialChars: {
 label: "Caractères spéciaux obligatoires";
 value: boolean;
 type: "switch";
 };

 passwordExpiry: {
 label: "Expiration (jours)";
 value: number; // 0 = jamais
 type: "number";
 min: 0;
 max: 365;
 };

 preventReuse: {
 label: "Empêcher réutilisation";
 value: number; // Nombre de derniers mots de passe
 type: "select";
 options: [0, 3, 5, 10];
 };
 };

 strengthIndicator: {
 currentStrength: "Fort" | "Moyen" | "Faible";
 color: string;
 suggestions: string[];
 };
 };

 sessionManagement: {
 title: "Gestion des sessions";
 settings: {
 sessionTimeout: {
 label: "Timeout d'inactivité (minutes)";
 value: number;
 type: "select";
 options: [15, 30, 60, 120, 480];
 };

 maxConcurrentSessions: {
 label: "Sessions simultanées max";
 value: number;
 type: "number";
 min: 1;
 max: 10;
 };

 rememberMe: {
 label: "Autoriser 'Se souvenir de moi'";
 value: boolean;
 type: "switch";
 duration: number; // jours si activé
 };

 forceLogoutOnPasswordChange: {
 label: "Déconnexion forcée après changement MDP";
 value: boolean;
 type: "switch";
 };
 };
 };

 twoFactorAuth: {
 title: "Authentification deux facteurs";
 enabled: boolean;
 toggle: () => void;

 methods: {
 sms: {
 enabled: boolean;
 phoneNumbers: string[];
 addPhone: () => void;
 };

 email: {
 enabled: boolean;
 emails: string[];
 addEmail: () => void;
 };

 authenticatorApp: {
 enabled: boolean;
 qrCode?: string;
 setup: () => void;
 };
 };

 enforcement: {
 mandatory: boolean;
 roles: string[]; // Rôles concernés
 gracePeriod: number; // jours
 };
 };
}
```

### Section Contrôle d'Accès
```typescript
interface AccessControlSection {
 title: " Contrôle d'Accès";

 roles: {
 title: "Rôles et permissions";
 list: Array<{
 id: string;
 name: string;
 description: string;
 permissions: string[];
 users: number; // Nombre d'utilisateurs
 isSystem: boolean; // Rôle système non modifiable
 color: string;
 }>;

 actions: {
 create: () => void;
 edit: (roleId: string) => void;
 delete: (roleId: string) => void;
 duplicate: (roleId: string) => void;
 };

 permissionMatrix: {
 modules: Array<{
 name: string;
 permissions: Array<{
 id: string;
 name: string;
 description: string;
 }>;
 }>;

 assignment: Record<string, string[]>; // roleId -> permissionIds
 onChange: (roleId: string, permissionId: string, granted: boolean) => void;
 };
 };

 users: {
 title: "Utilisateurs actifs";
 stats: {
 total: number;
 active: number;
 locked: number;
 pendingApproval: number;
 };

 recentActivity: Array<{
 userId: string;
 name: string;
 action: string;
 timestamp: Date;
 ip: string;
 device: string;
 }>;

 quickActions: {
 viewAll: () => void;
 inviteUser: () => void;
 exportList: () => void;
 };
 };

 ipWhitelist: {
 title: "Liste blanche IP";
 enabled: boolean;
 toggle: () => void;

 rules: Array<{
 id: string;
 name: string;
 ip: string; // IP ou CIDR
 type: "single" | "range" | "cidr";
 active: boolean;
 createdAt: Date;
 }>;

 actions: {
 add: () => void;
 remove: (id: string) => void;
 test: (ip: string) => boolean;
 };
 };
}
```

### Section Sécurité des Données
```typescript
interface DataSecuritySection {
 title: " Sécurité des Données";

 encryption: {
 title: "Chiffrement";

 atRest: {
 enabled: boolean;
 algorithm: "AES-256" | "AES-128";
 keyRotation: {
 enabled: boolean;
 frequency: "monthly" | "quarterly" | "yearly";
 lastRotation: Date;
 nextRotation: Date;
 };
 };

 inTransit: {
 enabled: boolean;
 tlsVersion: "1.2" | "1.3";
 certificateInfo: {
 issuer: string;
 validUntil: Date;
 fingerprint: string;
 };
 };

 sensitiveFields: {
 list: string[]; // Champs à chiffrer
 addField: (field: string) => void;
 removeField: (field: string) => void;
 };
 };

 backup: {
 title: "Sauvegardes";

 automatic: {
 enabled: boolean;
 frequency: "daily" | "weekly" | "monthly";
 time: string; // HH:mm
 retention: number; // jours
 };

 storage: {
 location: "local" | "cloud" | "both";
 encryption: boolean;
 compression: boolean;
 };

 lastBackups: Array<{
 id: string;
 date: Date;
 size: number;
 status: "success" | "failed" | "partial";
 type: "automatic" | "manual";
 }>;

 actions: {
 backupNow: () => void;
 restore: (backupId: string) => void;
 download: (backupId: string) => void;
 };
 };

 dataRetention: {
 title: "Rétention des données";

 policies: Array<{
 dataType: string;
 retention: number; // jours
 action: "delete" | "archive" | "anonymize";
 enabled: boolean;
 }>;

 gdprCompliance: {
 enabled: boolean;
 dataExportEnabled: boolean;
 dataDeletionEnabled: boolean;
 consentTracking: boolean;
 };
 };
}
```

### Section Logs et Audit
```typescript
interface LogsAuditSection {
 title: " Logs et Audit";

 auditLog: {
 enabled: boolean;

 events: Array<{
 category: string;
 events: Array<{
 name: string;
 logged: boolean;
 severity: "info" | "warning" | "critical";
 }>;
 }>;

 retention: {
 days: number;
 maxSize: number; // GB
 archiveOld: boolean;
 };

 search: {
 query: string;
 dateRange: [Date, Date];
 severity: string[];
 users: string[];
 actions: string[];
 onSearch: () => void;
 };

 recentEvents: Array<{
 id: string;
 timestamp: Date;
 user: string;
 action: string;
 resource: string;
 ip: string;
 status: "success" | "failed";
 details: any;
 }>;
 };

 securityAlerts: {
 title: "Alertes de sécurité";

 rules: Array<{
 id: string;
 name: string;
 condition: string;
 severity: "low" | "medium" | "high" | "critical";
 enabled: boolean;
 notifications: {
 email: boolean;
 sms: boolean;
 webhook: boolean;
 };
 }>;

 recentAlerts: Array<{
 id: string;
 rule: string;
 timestamp: Date;
 severity: string;
 message: string;
 resolved: boolean;
 }>;
 };
}
```

### Section API et Intégrations
```typescript
interface APIIntegrationsSection {
 title: " API et Intégrations";

 apiKeys: {
 title: "Clés API";

 keys: Array<{
 id: string;
 name: string;
 key: string; // Masquée partiellement
 created: Date;
 lastUsed: Date;
 expires: Date | null;
 permissions: string[];
 rateLimit: number;
 active: boolean;
 }>;

 actions: {
 create: () => void;
 regenerate: (id: string) => void;
 revoke: (id: string) => void;
 updatePermissions: (id: string, permissions: string[]) => void;
 };
 };

 webhooks: {
 title: "Webhooks";

 endpoints: Array<{
 id: string;
 url: string;
 events: string[];
 secret: string; // Masqué
 active: boolean;
 lastSuccess: Date;
 failureCount: number;
 }>;

 actions: {
 add: () => void;
 test: (id: string) => void;
 remove: (id: string) => void;
 viewLogs: (id: string) => void;
 };
 };

 cors: {
 title: "Configuration CORS";

 enabled: boolean;
 allowedOrigins: string[];
 allowedMethods: string[];
 allowedHeaders: string[];
 maxAge: number; // secondes

 actions: {
 addOrigin: (origin: string) => void;
 removeOrigin: (origin: string) => void;
 testOrigin: (origin: string) => boolean;
 };
 };
}
```

## État et données

```typescript
interface SecurityConfigState {
 // Configuration actuelle
 config: {
 authentication: AuthConfig;
 accessControl: AccessControlConfig;
 dataSecurity: DataSecurityConfig;
 logging: LoggingConfig;
 api: APIConfig;
 };

 // Statistiques
 stats: {
 securityScore: number; // 0-100
 lastAudit: Date;
 activeUsers: number;
 failedLogins24h: number;
 activeThreats: number;
 };

 // État des modifications
 changes: {
 pending: boolean;
 modified: string[]; // Sections modifiées
 canSave: boolean;
 };

 // Audit trail
 auditTrail: AuditEntry[];

 // Alertes actives
 alerts: SecurityAlert[];
}
```

## API Endpoints

```typescript
// Configuration
GET /api/security/config
PUT /api/security/config
POST /api/security/config/validate

// Audit
GET /api/security/audit/logs
GET /api/security/audit/report
POST /api/security/audit/run

// Gestion des accès
GET /api/security/roles
POST /api/security/roles
PUT /api/security/roles/:id
DELETE /api/security/roles/:id

// API Keys
GET /api/security/api-keys
POST /api/security/api-keys
PUT /api/security/api-keys/:id
DELETE /api/security/api-keys/:id
```

## Exemple d'implémentation

```tsx
export const SecurityConfigPage: React.FC = () => {
 const [config, setConfig] = useState<SecurityConfig>(defaultConfig);
 const [hasChanges, setHasChanges] = useState(false);
 const { save, validate, audit } = useSecurityConfig();

 const handleSave = async () => {
 const validation = await validate(config);
 if (validation.isValid) {
 await save(config);
 setHasChanges(false);
 }
 };

 return (
 <SecurityLayout>
 <SecurityConfigHeader
 onAudit={audit}
 onSave={handleSave}
 hasChanges={hasChanges}
 />

 <Tabs>
 <Tab label="Authentification">
 <AuthenticationSection
 config={config.authentication}
 onChange={(auth) => updateConfig({ authentication: auth })}
 />
 </Tab>

 <Tab label="Contrôle d'accès">
 <AccessControlSection
 config={config.accessControl}
 onChange={(access) => updateConfig({ accessControl: access })}
 />
 </Tab>

 <Tab label="Sécurité données">
 <DataSecuritySection
 config={config.dataSecurity}
 onChange={(data) => updateConfig({ dataSecurity: data })}
 />
 </Tab>

 <Tab label="Logs & Audit">
 <LogsAuditSection
 config={config.logging}
 onChange={(logs) => updateConfig({ logging: logs })}
 />
 </Tab>

 <Tab label="API & Intégrations">
 <APIIntegrationsSection
 config={config.api}
 onChange={(api) => updateConfig({ api: api })}
 />
 </Tab>
 </Tabs>
 </SecurityLayout>
 );
};
```