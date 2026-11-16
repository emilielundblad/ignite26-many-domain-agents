// Container Registry: admin user off, anonymous pull off, Entra-only pulls.
// azd builds images remotely in this registry (docker.remoteBuild in azure.yaml),
// so no local Docker is needed.

param location string
param tags object
param resourceToken string
param logAnalyticsWorkspaceId string

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
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
