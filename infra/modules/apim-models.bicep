// AI gateway route for one domain's model traffic: models/<domain>.
// Foundry projects reach it through an API Management connection
// (see foundry-connections.bicep). Shape follows Microsoft's foundry-samples
// "apim" connection guide: deployment in path, chat completions operation.

param apimName string
param domainKey string
param projectResourceId string
param tokensPerMinute int

resource apim 'Microsoft.ApiManagement/service@2024-06-01-preview' existing = {
  name: apimName
}

resource api 'Microsoft.ApiManagement/service/apis@2024-06-01-preview' = {
  parent: apim
  name: 'models-${domainKey}'
  properties: {
    displayName: 'Models (${domainKey})'
    description: 'Model access for the ${domainKey} domain: content safety, token budget, token metrics.'
    apiType: 'http'
    path: 'models/${domainKey}'
    protocols: ['https']
    subscriptionRequired: false
  }
}

resource chat 'Microsoft.ApiManagement/service/apis/operations@2024-06-01-preview' = {
  parent: api
  name: 'chat-completions'
  properties: {
    displayName: 'Chat completions'
    method: 'POST'
    urlTemplate: '/deployments/{deployment-id}/chat/completions'
    templateParameters: [
      {
        name: 'deployment-id'
        type: 'string'
        required: true
      }
    ]
  }
}

resource policy 'Microsoft.ApiManagement/service/apis/policies@2024-06-01-preview' = {
  parent: api
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: replace(replace(replace(loadTextContent('../policies/model-api.xml'), '__DOMAIN__', domainKey), '__PROJECT_ID__', projectResourceId), '__TPM__', string(tokensPerMinute))
  }
  dependsOn: [
    chat
  ]
}

output path string = api.properties.path
