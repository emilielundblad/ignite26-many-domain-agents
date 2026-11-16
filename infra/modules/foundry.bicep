// Microsoft Foundry: one account, one model deployment, one project per domain,
// tracing to Application Insights.
// Pattern follows Microsoft's foundry-samples (infrastructure-setup-bicep/40-basic-agent-setup).
// Keys are disabled on the account; everything uses Entra ID.

param location string
param tags object
param resourceToken string
param modelName string
param modelVersion string
param modelSkuName string
param modelCapacity int
param appInsightsName string
param principalId string
param principalType string

@description('Projects to create: name, displayName.')
param projects array

// Foundry User (previously Azure AI User). Lets the signed-in operator create and run agents.
var foundryUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'

resource appInsights 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: 'aif-ig26-${resourceToken}'
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: 'aif-ig26-${resourceToken}'
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: account
  name: modelName
  sku: {
    name: modelSkuName
    capacity: modelCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    raiPolicyName: 'Microsoft.DefaultV2'
  }
}

@batchSize(1)
resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = [for p in projects: {
  parent: account
  name: p.name
  location: location
  tags: union(tags, { domain: p.name })
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: p.displayName
    description: '${p.displayName} domain agents'
  }
  dependsOn: [
    deployment
  ]
}]

// Account-level connection so agents in every project export OpenTelemetry traces.
resource tracing 'Microsoft.CognitiveServices/accounts/connections@2025-06-01' = {
  parent: account
  name: 'appinsights'
  properties: {
    category: 'AppInsights'
    target: appInsights.id
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: appInsights.properties.ConnectionString
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: appInsights.id
    }
  }
}

resource operatorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(account.id, principalId, foundryUserRoleId)
  scope: account
  properties: {
    principalId: principalId
    principalType: principalType
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
  }
}

output accountName string = account.name
output accountId string = account.id
output openAiEndpoint string = 'https://${account.properties.customSubDomainName}.openai.azure.com/openai'
output modelDeploymentName string = deployment.name
output projectIds array = [for (p, i) in projects: project[i].id]
output projectEndpoints object = toObject(projects, p => p.name, p => 'https://${account.properties.customSubDomainName}.services.ai.azure.com/api/projects/${p.name}')
