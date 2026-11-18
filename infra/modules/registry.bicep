// Container Registry: admin user off, anonymous pull off, Entra-only pulls.
// azd builds images remotely in this registry (docker.remoteBuild in azure.yaml),
// so no local Docker is needed.

param location string
param tags object
param resourceToken string
param logAnalyticsWorkspaceId string

resource acr 'Microsoft.ContainerRegistry/registries@2025-05-01-preview' = {
  name: 'crig26${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    adminUserEnabled: false
    anonymousPullEnabled: false
    publicNetworkAccess: 'Enabled'
    // Legacy (registry-wide) role assignment mode, so the AcrPull role assignment in
    // modules/roles.bicep grants image pulls. The ABAC repository-permissions mode
    // ignores AcrPull: https://learn.microsoft.com/azure/container-registry/container-registry-rbac-abac-repository-permissions
    roleAssignmentMode: 'LegacyRegistryPermissions'
    policies: {
      retentionPolicy: {
        status: 'disabled'
      }
    }
  }
}

resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: acr
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'audit'
        enabled: true
      }
    ]
  }
}

output name string = acr.name
output id string = acr.id
output loginServer string = acr.properties.loginServer
