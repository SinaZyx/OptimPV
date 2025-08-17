# Script PowerShell pour configurer HTTPS sur Windows avec IIS
# Exécuter en tant qu'Administrateur

Write-Host "======================================"
Write-Host "Configuration HTTPS pour OptimPV (Windows)"
Write-Host "======================================"

# Variables à personnaliser
$domain = "localhost"  # Changez pour votre domaine
$certPath = "C:\Certificates"
$iisPort = 443
$streamlitPort = 8501

# 1. Activer IIS et les fonctionnalités nécessaires
Write-Host "[1/5] Installation IIS et modules..."
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole, IIS-WebServer, IIS-CommonHttpFeatures, IIS-HttpErrors, IIS-HttpRedirect, IIS-ApplicationDevelopment, IIS-HealthAndDiagnostics, IIS-HttpLogging, IIS-Security, IIS-RequestFiltering, IIS-URLAuthorization, IIS-WindowsAuthentication, IIS-WebServerManagementTools, IIS-ManagementConsole -All

# 2. Installer URL Rewrite et ARR (Application Request Routing)
Write-Host "[2/5] Installation URL Rewrite et ARR..."
Write-Host "Téléchargez et installez manuellement :"
Write-Host "- URL Rewrite : https://www.iis.net/downloads/microsoft/url-rewrite"
Write-Host "- ARR : https://www.iis.net/downloads/microsoft/application-request-routing"
Write-Host "Appuyez sur Entrée quand c'est fait..."
Read-Host

# 3. Créer un certificat auto-signé (pour test local)
Write-Host "[3/5] Création certificat auto-signé..."
New-Item -ItemType Directory -Path $certPath -Force
$cert = New-SelfSignedCertificate -DnsName $domain -CertStoreLocation "cert:\LocalMachine\My" -FriendlyName "OptimPV Certificate"
$certThumbprint = $cert.Thumbprint
Write-Host "Certificat créé : $certThumbprint"

# 4. Créer configuration IIS
Write-Host "[4/5] Configuration IIS..."

# Créer le fichier web.config pour le reverse proxy
$webConfig = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="ReverseProxy to Streamlit" stopProcessing="true">
                    <match url="(.*)" />
                    <action type="Rewrite" url="http://localhost:$streamlitPort/{R:1}" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_HOST" value="{HTTP_HOST}" />
                        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
                    </serverVariables>
                </rule>
            </rules>
        </rewrite>
        <httpProtocol>
            <customHeaders>
                <add name="X-Frame-Options" value="SAMEORIGIN" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>
"@

# Sauvegarder web.config
$webConfig | Out-File -FilePath "C:\inetpub\wwwroot\web.config" -Encoding UTF8

# 5. Configurer le site IIS
Write-Host "[5/5] Configuration du site IIS..."
Import-Module WebAdministration

# Supprimer le site par défaut s'il existe
if (Get-Website -Name "Default Web Site" -ErrorAction SilentlyContinue) {
    Remove-Website -Name "Default Web Site"
}

# Créer nouveau site pour OptimPV
New-Website -Name "OptimPV" -Port 443 -Ssl -PhysicalPath "C:\inetpub\wwwroot" -HostHeader $domain

# Lier le certificat
$binding = Get-WebBinding -Name "OptimPV" -Protocol https
$binding.AddSslCertificate($certThumbprint, "My")

# Activer le proxy dans ARR
Set-WebConfigurationProperty -PSPath 'MACHINE/WEBROOT/APPHOST' -Filter "system.webServer/proxy" -Name "enabled" -Value "True"

# Démarrer IIS
Start-Service W3SVC

Write-Host "======================================"
Write-Host "Configuration terminée !"
Write-Host "======================================"
Write-Host ""
Write-Host "IMPORTANT :"
Write-Host "1. Lancez OptimPV : streamlit run app.py"
Write-Host "2. Accédez à : https://$domain"
Write-Host "3. Acceptez l'avertissement du certificat auto-signé"
Write-Host ""
Write-Host "Pour un vrai certificat SSL :"
Write-Host "- Utilisez Let's Encrypt avec win-acme"
Write-Host "- Ou achetez un certificat commercial"