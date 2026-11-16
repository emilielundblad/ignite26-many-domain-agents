// All resources, in one resource group. Called from main.bicep.

param location string
param tags object
param resourceToken string
param principalId string
param principalType string
param mcpGatewayAppId string
param apimPublisherEmail string
param modelName string
param modelVersion string
param modelSkuName string
param modelCapacity int
param supportTokensPerMinute int
param docsTokensPerMinute int
param alertEmail string
param enableAppGateway bool
param appGatewayHostName string
param appGatewayCertificateUri string

// One entry per business domain. `enabled: false` means the domain's backend and
// MCP server exist, but no agent is created for it and no other domain may call it.
var domains = [
  {
    key: 'support'
    displayName: 'Support'
    enabled: true
    appRole: 'Support.Tools'
    serviceName: 'ticketing-api'
    containerAppName: 'ca-ig26-ticketing-api'
    restApiName: 'rest-support-tickets'
    restApiPath: 'rest/support-tickets'
    mcpName: 'mcp-support-tickets'
    mcpDisplayName: 'Support tickets (MCP)'
    openApi: loadTextContent('../apps/ticketing-api/openapi.json')
    tools: ['list-tickets', 'get-ticket', 'add-ticket-note']
  }
  {
    key: 'docs'
    displayName: 'Documentation'
    enabled: true
    appRole: 'Docs.Tools'
    serviceName: 'knowledge-api'
    containerAppName: 'ca-ig26-knowledge-api'
    restApiName: 'rest-docs-knowledge'
    restApiPath: 'rest/docs-knowledge'
    mcpName: 'mcp-docs-knowledge'
    mcpDisplayName: 'Product knowledge (MCP)'
    openApi: loadTextContent('../apps/knowledge-api/openapi.json')
    tools: ['search-articles', 'get-article']
  }
  {
    key: 'custops'
    displayName: 'Customer operations'
    enabled: false
    appRole: 'CustOps.Tools'
    serviceName: 'creditnote-api'
    containerAppName: 'ca-ig26-creditnote-api'
    restApiName: 'rest-custops-creditnotes'
    restApiPath: 'rest/custops-creditnotes'
    mcpName: 'mcp-custops-creditnotes'
    mcpDisplayName: 'Credit notes (MCP)'
    openApi: loadTextContent('../apps/creditnote-api/openapi.json')
    tools: ['create-credit-note']
  }
]

module network 'modules/network.bicep' = {
  name: 'network'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
  }
}

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    alertEmail: alertEmail
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    privateEndpointSubnetId: network.outputs.backendSubnetId
    privateDnsZoneId: network.outputs.keyVaultPrivateDnsZoneId
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module registry 'modules/registry.bicep' = {
  name: 'registry'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module containerApps 'modules/container-apps.bicep' = {
  name: 'container-apps'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    infrastructureSubnetId: network.outputs.containerAppsSubnetId
    vnetId: network.outputs.vnetId
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    registryName: registry.outputs.name
    registryLoginServer: registry.outputs.loginServer
    apps: [for d in domains: {
      name: d.containerAppName
      serviceName: d.serviceName
      domain: d.key
    }]
  }
}

module contentSafety 'modules/content-safety.bicep' = {
  name: 'content-safety'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
  }
}

module foundry 'modules/foundry.bicep' = {
  name: 'foundry'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    modelName: modelName
    modelVersion: modelVersion
    modelSkuName: modelSkuName
    modelCapacity: modelCapacity
    appInsightsName: monitoring.outputs.appInsightsName
    principalId: principalId
    principalType: principalType
    projects: [for d in domains: {
      name: d.key
      displayName: d.displayName
    }]
  }
}

module apim 'modules/apim.bicep' = {
  name: 'apim'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    publisherEmail: apimPublisherEmail
    subnetId: network.outputs.apimSubnetId
    appInsightsName: monitoring.outputs.appInsightsName
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    mcpGatewayAppId: mcpGatewayAppId
    contentSafetyEndpoint: contentSafety.outputs.endpoint
    foundryOpenAiEndpoint: foundry.outputs.openAiEndpoint
  }
}

module roles 'modules/roles.bicep' = {
  name: 'roles'
  params: {
    apimPrincipalId: apim.outputs.principalId
    contentSafetyName: contentSafety.outputs.name
    foundryAccountName: foundry.outputs.accountName
  }
}

module domainApis 'modules/apim-domain.bicep' = [for d in domains: {
  name: 'apim-domain-${d.key}'
  params: {
    apimName: apim.outputs.name
    domainKey: d.key
    domainDisplayName: d.displayName
    appRole: d.appRole
    restApiName: d.restApiName
    restApiPath: d.restApiPath
    openApi: d.openApi
    backendUrl: 'https://${d.containerAppName}.${containerApps.outputs.defaultDomain}'
    mcpName: d.mcpName
    mcpDisplayName: d.mcpDisplayName
    tools: d.tools
  }
}]

module modelApis 'modules/apim-models.bicep' = [for d in filter(domains, x => x.enabled): {
  name: 'apim-models-${d.key}'
  params: {
    apimName: apim.outputs.name
    domainKey: d.key
    projectResourceId: foundry.outputs.projectIds[indexOf(map(domains, x => x.key), d.key)]
    tokensPerMinute: d.key == 'support' ? supportTokensPerMinute : docsTokensPerMinute
  }
  dependsOn: [
    roles
  ]
}]

// Project connections: models through the AI gateway, tools through governed MCP.
// The Support project is deliberately also given the Customer ops MCP server, so
// Demo 2 can show the gateway denying it.
module supportConnections 'modules/foundry-connections.bicep' = {
  name: 'foundry-connections-support'
  params: {
    accountName: foundry.outputs.accountName
    projectName: 'support'
    apimGatewayUrl: apim.outputs.gatewayUrl
    modelApiPath: 'models/support'
    modelDeploymentName: foundry.outputs.modelDeploymentName
    modelName: modelName
    modelVersion: modelVersion
    mcpGatewayAppId: mcpGatewayAppId
    mcpServers: [
      domains[0].mcpName
      domains[1].mcpName
      domains[2].mcpName
    ]
  }
  dependsOn: [
    domainApis
    modelApis
  ]
}

module docsConnections 'modules/foundry-connections.bicep' = {
  name: 'foundry-connections-docs'
  params: {
    accountName: foundry.outputs.accountName
    projectName: 'docs'
    apimGatewayUrl: apim.outputs.gatewayUrl
    modelApiPath: 'models/docs'
    modelDeploymentName: foundry.outputs.modelDeploymentName
    modelName: modelName
    modelVersion: modelVersion
    mcpGatewayAppId: mcpGatewayAppId
    mcpServers: [
      domains[1].mcpName
    ]
  }
  dependsOn: [
    domainApis
    modelApis
  ]
}

module appGateway 'modules/app-gateway.bicep' = if (enableAppGateway) {
  name: 'app-gateway'
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    subnetId: network.outputs.appGatewaySubnetId
    hostName: appGatewayHostName
    certificateUri: appGatewayCertificateUri
    keyVaultName: keyVault.outputs.name
    apimGatewayHostName: replace(apim.outputs.gatewayUrl, 'https://', '')
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    actionGroupId: monitoring.outputs.actionGroupId
  }
}

module alerts 'modules/alerts.bicep' = {
  name: 'alerts'
  params: {
    tags: tags
    apimName: apim.outputs.name
    actionGroupId: monitoring.outputs.actionGroupId
  }
}

output containerRegistryEndpoint string = registry.outputs.loginServer
output containerRegistryName string = registry.outputs.name
output apimName string = apim.outputs.name
output apimGatewayUrl string = apim.outputs.gatewayUrl
output foundryAccountName string = foundry.outputs.accountName
output projectEndpoints object = foundry.outputs.projectEndpoints
output modelDeploymentName string = foundry.outputs.modelDeploymentName
output modelGatewayConnectionName string = supportConnections.outputs.modelGatewayConnectionName
output logAnalyticsCustomerId string = monitoring.outputs.logAnalyticsCustomerId
output appInsightsName string = monitoring.outputs.appInsightsName
