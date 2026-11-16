// Resource-group part of deploy-identity.bicep.

param location string
param githubOidcSubject string
param rbacCondition string

var contributorRoleId = 'b24988ac-6180-42a0-ab88-20f7382dd24c'
var rbacAdminRoleId = 'f58310d9-a9f6-439a-9e8d-f62e7b41a168'

resource id 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-ig26-deploy'
  location: location
  tags: {
    event: 'ignite2026'
  }
}

resource fic 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: id
  name: 'github-demo-environment'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: githubOidcSubject
    audiences: ['api://AzureADTokenExchange']
  }
}

resource contributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, id.id, contributorRoleId)
  properties: {
    principalId: id.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', contributorRoleId)
  }
}

resource rbacAdmin 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, id.id, rbacAdminRoleId)
  properties: {
    principalId: id.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', rbacAdminRoleId)
    condition: rbacCondition
    conditionVersion: '2.0'
    description: 'Only the built-in roles this template assigns, only to service principals.'
  }
}

output principalId string = id.properties.principalId
output clientId string = id.properties.clientId
