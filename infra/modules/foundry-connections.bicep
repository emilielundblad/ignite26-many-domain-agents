// Project connections for one domain:
//  1. ig26-models: the domain's model route in API Management, authenticated with
//     the project managed identity (no API key). Agents use the model as
//     "ig26-models/<deployment>".
//     https://github.com/microsoft-foundry/foundry-samples/tree/main/infrastructure/infrastructure-setup-bicep/01-connections/apim
//  2. One RemoteTool connection per MCP server, authenticated with the agent's
//     own Entra agent identity (authType AgenticIdentityToken). The audience is the
//     governed MCP gateway app, not the MCP URL.
//     https://learn.microsoft.com/azure/foundry/agents/how-to/mcp-authentication
//     https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity

param accountName string
param projectName string
param apimGatewayUrl string
param modelApiPath string
param modelDeploymentName string
param modelName string
param modelVersion string
param mcpGatewayAppId string
param mcpServers array

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: accountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: account
  name: projectName
}

resource models 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = {
  parent: project
  name: 'ig26-models'
  properties: {
    category: 'ApiManagement'
    target: '${apimGatewayUrl}/${modelApiPath}'
    // Valid service value (used by azd ai connection create); missing from the Bicep type definitions.
    #disable-next-line BCP036
    authType: 'ProjectManagedIdentity'
    #disable-next-line BCP037
    audience: 'https://cognitiveservices.azure.com'
    isSharedToAll: true
    credentials: {}
    metadata: {
      deploymentInPath: 'true'
      inferenceAPIVersion: '2024-10-21'
      models: string([
        {
          name: modelDeploymentName
          properties: {
            model: {
              name: modelName
              version: modelVersion
              format: 'OpenAI'
            }
          }
        }
      ])
    }
  }
}

resource mcp 'Microsoft.CognitiveServices/accounts/projects/connections@2025-04-01-preview' = [for server in mcpServers: {
  parent: project
  name: server
  properties: {
    category: 'RemoteTool'
    target: '${apimGatewayUrl}/${server}/mcp'
    // Valid service value (used by azd ai connection create); missing from the Bicep type definitions.
    #disable-next-line BCP036
    authType: 'AgenticIdentityToken'
    #disable-next-line BCP037
    audience: 'api://${mcpGatewayAppId}'
    isSharedToAll: true
    metadata: {
      type: 'mcp'
    }
  }
}]

output modelGatewayConnectionName string = models.name
