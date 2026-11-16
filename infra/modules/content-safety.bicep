// Azure AI Content Safety, used by the llm-content-safety policy in API
// Management. Keys are disabled; API Management calls it with its managed identity.

param location string
param tags object
param resourceToken string

resource cs 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: 'cs-ig26-${resourceToken}'
  location: location
  tags: tags
  kind: 'ContentSafety'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: 'cs-ig26-${resourceToken}'
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
  }
}

output name string = cs.name
output endpoint string = cs.properties.endpoint
