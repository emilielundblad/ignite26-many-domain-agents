// API Management Standard v2: the single governed entry for models and tools.
// Public gateway endpoint (Foundry Agent Service calls it), outbound VNet
// integration so it can reach the internal Container Apps environment.
// https://learn.microsoft.com/azure/api-management/integrate-vnet-outbound
// MCP servers are supported on Standard v2 and not in workspaces:
// https://learn.microsoft.com/azure/api-management/mcp-server-overview

param location string
param tags object
param resourceToken string
param publisherEmail string
param subnetId string
param appInsightsName string
param logAnalyticsWorkspaceId string
param mcpGatewayAppId string
param contentSafetyEndpoint string
param foundryOpenAiEndpoint string

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource apim 'Microsoft.ApiManagement/service@2024-06-01-preview' = {
  name: 'apim-ig26-${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'StandardV2'
    capacity: 1
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    publisherEmail: publisherEmail
    publisherName: 'Ignite 2026 lab'
    virtualNetworkType: 'External'
    virtualNetworkConfiguration: {
      subnetResourceId: subnetId
    }
    publicNetworkAccess: 'Enabled'
    customProperties: {
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11': 'False'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30': 'False'
    }
  }
}

resource tenantIdValue 'Microsoft.ApiManagement/service/namedValues@2024-06-01-preview' = {
  parent: apim
  name: 'ig26-tenant-id'
  properties: {
    displayName: 'ig26-tenant-id'
    value: tenant().tenantId
    secret: false
  }
}

resource gatewayAppIdValue 'Microsoft.ApiManagement/service/namedValues@2024-06-01-preview' = {
  parent: apim
  name: 'ig26-mcp-gateway-app-id'
  properties: {
    displayName: 'ig26-mcp-gateway-app-id'
    value: mcpGatewayAppId
    secret: false
  }
}

resource restScopeAuthValue 'Microsoft.ApiManagement/service/namedValues@2024-06-01-preview' = {
  parent: apim
  name: 'ig26-rest-scope-auth'
  properties: {
    displayName: 'ig26-rest-scope-auth'
    value: 'on'
    secret: false
  }
}

resource logger 'Microsoft.ApiManagement/service/loggers@2024-06-01-preview' = {
  parent: apim
  name: 'appinsights'
  properties: {
    loggerType: 'applicationInsights'
    resourceId: appInsights.id
    credentials: {
      connectionString: appInsights.properties.ConnectionString
    }
  }
}

// Service-wide App Insights diagnostics: W3C trace context so Foundry traces and
// gateway requests correlate. No request or response bodies are logged.
resource diagnostics 'Microsoft.ApiManagement/service/diagnostics@2024-06-01-preview' = {
  parent: apim
  name: 'applicationinsights'
  properties: {
    loggerId: logger.id
    alwaysLog: 'allErrors'
    httpCorrelationProtocol: 'W3C'
    verbosity: 'information'
    logClientIp: false
    metrics: true
    sampling: {
      samplingType: 'fixed'
      percentage: 100
    }
  }
}

resource azureMonitorDiag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: apim
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logAnalyticsDestinationType: 'Dedicated'
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource contentSafetyBackend 'Microsoft.ApiManagement/service/backends@2024-06-01-preview' = {
  parent: apim
  name: 'ig26-content-safety'
  properties: {
    description: 'Azure AI Content Safety, managed identity auth'
    url: contentSafetyEndpoint
    protocol: 'http'
    credentials: {
      #disable-next-line BCP037
      managedIdentity: {
        resource: 'https://cognitiveservices.azure.com'
      }
    }
  }
}

resource foundryBackend 'Microsoft.ApiManagement/service/backends@2024-06-01-preview' = {
  parent: apim
  name: 'ig26-foundry-openai'
  properties: {
    description: 'Foundry model deployments, managed identity auth'
    url: foundryOpenAiEndpoint
    protocol: 'http'
    credentials: {
      #disable-next-line BCP037
      managedIdentity: {
        resource: 'https://cognitiveservices.azure.com'
      }
    }
  }
}

resource authorizeFragment 'Microsoft.ApiManagement/service/policyFragments@2024-06-01-preview' = {
  parent: apim
  name: 'ig26-authorize-agent'
  properties: {
    description: 'Domain boundary: validate the agent token and require the domain app role.'
    format: 'rawxml'
    value: loadTextContent('../policies/fragment-authorize-agent.xml')
  }
  dependsOn: [
    tenantIdValue
    gatewayAppIdValue
  ]
}

resource globalPolicy 'Microsoft.ApiManagement/service/policies@2024-06-01-preview' = {
  parent: apim
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: loadTextContent('../policies/global.xml')
  }
}

output name string = apim.name
output id string = apim.id
output gatewayUrl string = apim.properties.gatewayUrl
output principalId string = apim.identity.principalId
