#Requires -Version 7.0
<#
.SYNOPSIS
Create (or reuse) the Entra application that represents the governed MCP gateway,
using PowerShell 7 and the Microsoft Graph PowerShell SDK.

.DESCRIPTION
PowerShell twin of identity/setup_gateway_app.py, suited to on-screen demos of the
Entra creation steps (demo 1). Idempotent, no credentials: the app only receives
tokens, nothing ever signs in as it.

Creates, with your own delegated rights:
- App registration ig26-mcp-gateway-<env>: single tenant, identifier URI
  api://<appId>, v2 access tokens, three application-only app roles
  (Support.Tools, Docs.Tools, CustOps.Tools).
- Its service principal with "assignment required" on.

Role IDs are deterministic (UUIDv5, same namespace as the Python script), so both
scripts can be mixed freely.

.EXAMPLE
pwsh -File identity/setup_gateway_app.ps1            # uses AZURE_ENV_NAME from azd
pwsh -File identity/setup_gateway_app.ps1 -EnvironmentName ig26lab2
#>
[CmdletBinding()]
param(
    [string]$EnvironmentName = $env:AZURE_ENV_NAME,
    # Skip writing MCP_GATEWAY_APP_ID / MCP_GATEWAY_SP_ID back to the azd environment.
    [switch]$NoAzdEnv
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $EnvironmentName) {
    $EnvironmentName = (& azd env get-value AZURE_ENV_NAME 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $EnvironmentName) {
        throw 'No environment name. Pass -EnvironmentName or run inside an azd environment.'
    }
}

# Same namespace as identity/setup_gateway_app.py: both produce identical role IDs.
$RoleNamespace = [guid]'6f1c3c63-0e4e-4f3f-9a54-6b7d1f2a2a26'
$AppRoles = @(
    @{ Value = 'Support.Tools'; Name = 'Support domain tools';          Desc = 'Call the Support domain MCP tools (tickets).' }
    @{ Value = 'Docs.Tools';    Name = 'Documentation domain tools';    Desc = 'Call the Documentation domain MCP tools (product knowledge).' }
    @{ Value = 'CustOps.Tools'; Name = 'Customer operations tools';     Desc = 'Call the Customer operations MCP tools (credit notes). Not granted to any agent in this lab.' }
)

function New-Uuid5 {
    param([guid]$Namespace, [string]$Name)
    # RFC 4122 UUIDv5: SHA-1 over namespace (network byte order) + name.
    $ns = $Namespace.ToByteArray()
    [Array]::Reverse($ns, 0, 4); [Array]::Reverse($ns, 4, 2); [Array]::Reverse($ns, 6, 2)
    $sha1 = [System.Security.Cryptography.SHA1]::Create()
    try { $hash = $sha1.ComputeHash($ns + [System.Text.Encoding]::UTF8.GetBytes($Name)) }
    finally { $sha1.Dispose() }
    $b = $hash[0..15]
    $b[6] = ($b[6] -band 0x0F) -bor 0x50   # version 5
    $b[8] = ($b[8] -band 0x3F) -bor 0x80   # RFC 4122 variant
    [Array]::Reverse($b, 0, 4); [Array]::Reverse($b, 4, 2); [Array]::Reverse($b, 6, 2)
    [guid]::new([byte[]]$b)
}

function Get-DesiredRoles {
    @($AppRoles | ForEach-Object {
        @{
            Id                 = (New-Uuid5 -Namespace $RoleNamespace -Name $_.Value).Guid
            Value              = $_.Value
            DisplayName        = $_.Name
            Description        = $_.Desc
            AllowedMemberTypes = @('Application')
            IsEnabled          = $true
        }
    })
}

foreach ($module in 'Microsoft.Graph.Authentication', 'Microsoft.Graph.Applications') {
    if (-not (Get-Module -ListAvailable -Name $module)) {
        Write-Host "Installing $module (CurrentUser scope)"
        Install-Module $module -Scope CurrentUser -Repository PSGallery -Force
    }
}
Import-Module Microsoft.Graph.Authentication, Microsoft.Graph.Applications

# Delegated sign-in, your own rights; no secrets anywhere.
Connect-MgGraph -Scopes 'Application.ReadWrite.All' -NoWelcome

$displayName = "ig26-mcp-gateway-$EnvironmentName"
$app = Get-MgApplication -Filter "displayName eq '$displayName'" -All
if ($app -is [array] -and $app.Count -gt 1) {
    throw "More than one application is named $displayName. Delete the extras or set MCP_GATEWAY_APP_ID yourself."
}

if ($app) {
    Write-Host "Reusing app registration $displayName ($($app.AppId))"
} else {
    $app = New-MgApplication -DisplayName $displayName -SignInAudience 'AzureADMyOrg' `
        -Notes 'Ignite 2026 lab: audience for agent tokens to the governed MCP gateway in API Management. No credentials by design.' `
        -Tags @('ig26', 'event:ignite2026') `
        -Api @{ RequestedAccessTokenVersion = 2 } `
        -AppRoles (Get-DesiredRoles)
    Write-Host "Created app registration $displayName ($($app.AppId))"
}

$patch = @{}
$uri = "api://$($app.AppId)"
if ($app.IdentifierUris -notcontains $uri) { $patch.IdentifierUris = @($uri) }
$existingValues = @($app.AppRoles | ForEach-Object Value)
$missing = @(Get-DesiredRoles | Where-Object { $_.Value -notin $existingValues })
if ($missing) { $patch.AppRoles = @($app.AppRoles) + $missing }
if ($app.Api.RequestedAccessTokenVersion -ne 2) { $patch.Api = @{ RequestedAccessTokenVersion = 2 } }
if ($patch.Count) { Update-MgApplication -ApplicationId $app.Id @patch }

$sp = Get-MgServicePrincipal -Filter "appId eq '$($app.AppId)'" -All | Select-Object -First 1
if (-not $sp) {
    $sp = New-MgServicePrincipal -AppId $app.AppId -Tags @('HideApp', 'ig26')
    Write-Host "Created service principal $($sp.Id)"
}
if (-not $sp.AppRoleAssignmentRequired) {
    Update-MgServicePrincipal -ServicePrincipalId $sp.Id -AppRoleAssignmentRequired:$true
}

if (-not $NoAzdEnv) {
    & azd env set MCP_GATEWAY_APP_ID $app.AppId
    & azd env set MCP_GATEWAY_SP_ID $sp.Id
}

Write-Host "MCP gateway app ready. Audience: api://$($app.AppId). App roles: $(@($AppRoles.Value) -join ', ')."
