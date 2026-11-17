// One business domain in API Management:
//   REST API imported from the backend's OpenAPI document (operations = tools)
//   MCP server exposing selected operations as MCP tools
//   a product grouping both, so the domain is visible as one unit
// Pattern from https://learn.microsoft.com/azure/api-management/export-rest-mcp-server
// and the Azure-Samples/AI-Gateway "mcp-from-api" lab (MIT).

param apimName string
param domainKey string
param domainDisplayName string
param appRole string
param restApiName string
param restApiPath string
param openApi string
param backendUrl string
param mcpName string
param mcpDisplayName string
param tools array

resource apim 'Microsoft.ApiManagement/service@2024-06-01-preview' existing = {
  name: apimName
}

resource restApi 'Microsoft.ApiManagement/service/apis@2024-06-01-preview' = {
  parent: apim
  name: restApiName
  properties: {
    displayName: '${domainDisplayName} REST (behind ${mcpName})'
    apiType: 'http'
    path: restApiPath
    protocols: ['https']
    subscriptionRequired: false
    serviceUrl: backendUrl
    format: 'openapi+json'
    value: openApi
    isCurrent: true
  }
}

resource restPolicy 'Microsoft.ApiManagement/service/apis/policies@2024-06-01-preview' = {
  parent: restApi
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: replace(replace(loadTextContent('../policies/rest-api.xml'), '__APP_ROLE__', appRole), '__REST_NAME__', restApiName)
  }
}

resource operations 'Microsoft.ApiManagement/service/apis/operations@2024-06-01-preview' existing = [for t in tools: {
  parent: restApi
  name: t
}]

resource mcp 'Microsoft.ApiManagement/service/apis@2025-09-01-preview' = {
  parent: apim
  name: mcpName
  properties: {
    // MCP servers are managed with API version 2025-09-01-preview or later, as an
    // API of type `mcp` with tools as apis/tools child resources:
    // https://learn.microsoft.com/azure/api-management/manage-mcp-servers-rest-api
    type: 'mcp'
    displayName: mcpDisplayName
    description: '${domainDisplayName} domain tools. Callers need the ${appRole} app role on the gateway app.'
    path: mcpName
    protocols: ['https']
    subscriptionRequired: false
  }
  dependsOn: [
    restPolicy
  ]
}

// One tool per selected REST operation. Tools are child resources, so they can be
// added, renamed or removed without recreating the MCP server.
// https://learn.microsoft.com/azure/templates/microsoft.apimanagement/2025-09-01-preview/service/apis/tools
resource mcpToolResources 'Microsoft.ApiManagement/service/apis/tools@2025-09-01-preview' = [for (t, i) in tools: {
  parent: mcp
  name: t
  properties: {
    displayName: t
    description: operations[i].properties.description
    operationId: operations[i].id
  }
}]

resource mcpPolicy 'Microsoft.ApiManagement/service/apis/policies@2025-09-01-preview' = {
  parent: mcp
  name: 'policy'
  properties: {
    format: 'rawxml'
    value: replace(replace(loadTextContent('../policies/mcp-server.xml'), '__APP_ROLE__', appRole), '__MCP_NAME__', mcpName)
  }
}

resource product 'Microsoft.ApiManagement/service/products@2024-06-01-preview' = {
  parent: apim
  name: 'prod-${domainKey}'
  properties: {
    displayName: '${domainDisplayName} domain'
    description: 'APIs and MCP servers owned by the ${domainDisplayName} domain.'
    subscriptionRequired: false
    state: 'published'
  }
}

resource productRest 'Microsoft.ApiManagement/service/products/apis@2024-06-01-preview' = {
  parent: product
  name: restApi.name
}

resource productMcp 'Microsoft.ApiManagement/service/products/apis@2024-06-01-preview' = {
  parent: product
  name: mcp.name
}

output mcpEndpoint string = '${apim.properties.gatewayUrl}/${mcpName}/mcp'
