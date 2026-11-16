// Data-plane roles for the API Management managed identity. Narrowest built-in
// roles, scoped to the single resource each one is needed on.

param apimPrincipalId string
param contentSafetyName string
param foundryAccountName string

var cognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908'
var cognitiveServicesOpenAiUserRoleId = '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'

resource contentSafety 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: contentSafetyName
}

resource foundry 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

// API Management calls Content Safety for llm-content-safety.
resource apimContentSafety 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(contentSafety.id, apimPrincipalId, cognitiveServicesUserRoleId)
  scope: contentSafety
  properties: {
    principalId: apimPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRoleId)
  }
}

// API Management calls the Foundry model deployment on behalf of the projects (AI gateway).
resource apimFoundry 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundry.id, apimPrincipalId, cognitiveServicesOpenAiUserRoleId)
  scope: foundry
  properties: {
    principalId: apimPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesOpenAiUserRoleId)
  }
}
