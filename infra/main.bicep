// Many Domain Agents, One Governance Model: reference deployment.
// Deployed by `azd provision` (or `azd up`). Subscription scope: creates one resource group.
targetScope = 'subscription'

@minLength(1)
@maxLength(20)
@description('azd environment name, used in resource names and the azd-env-name tag.')
param environmentName string

@minLength(1)
@description('Region for all resources. Must offer API Management Standard v2, Azure Container Apps workload profiles, Microsoft Foundry Agent Service and the chosen model as GlobalStandard.')
param location string

@description('Object ID of the person running azd. Gets Foundry User on the Foundry account so the setup scripts can create agents. Filled by azd from your signed-in identity.')
param principalId string = ''

@allowed(['User', 'ServicePrincipal'])
param principalType string = 'User'

@description('Application (client) ID of the Entra app that represents the governed MCP gateway. Created by the preprovision hook (identity/setup_gateway_app.py).')
param mcpGatewayAppId string

@description('Publisher email shown on the API Management instance. Use a team or lab mailbox.')
param apimPublisherEmail string = 'noreply@example.com'

@description('Model deployed in Foundry for the agents.')
param modelName string = 'gpt-4.1-mini'
param modelVersion string = '2025-04-14'
param modelSkuName string = 'GlobalStandard'
@description('Model capacity in thousands of tokens per minute.')
param modelCapacity int = 50

@description('Tokens per minute the Support domain may use through the AI gateway. Kept low on purpose so Demo 3 can show a 429.')
param supportTokensPerMinute int = 4000
@description('Tokens per minute the Documentation domain may use through the AI gateway.')
param docsTokensPerMinute int = 40000

@description('Optional email address for alerts. Leave empty to skip the action group.')
param alertEmail string = ''

@description('Deploy Application Gateway WAF_v2 in front of the API Management gateway. Needs a custom domain and a certificate in Key Vault, so it is off by default.')
param enableAppGateway bool = false
@description('Host name for the Application Gateway listener, for example gateway.ig26.contoso.example. Required when enableAppGateway is true.')
param appGatewayHostName string = ''
@description('Versionless Key Vault secret ID of the PFX certificate for appGatewayHostName. Required when enableAppGateway is true.')
param appGatewayCertificateUri string = ''

@description('Value of the owner tag (your alias).')
param ownerTag string = 'ig26-lab'
@description('Value of the teardown tag.')
param teardownTag string = 'after-2026-11-30'
@description('Value of the deletiondate tag. Lab subscriptions with lifecycle automation often delete resources that lack it; set it to the date the lab may be removed.')
param deletionDateTag string = '2026-12-05'

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var tags = {
  event: 'ignite2026'
  'azd-env-name': environmentName
  owner: ownerTag
  teardown: teardownTag
  deletiondate: deletionDateTag
}

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-ig26-${environmentName}'
  location: location
  tags: tags
}

module resources 'resources.bicep' = {
  name: 'ig26-resources'
  scope: rg
  params: {
    location: location
    tags: tags
    resourceToken: resourceToken
    principalId: principalId
    principalType: principalType
    mcpGatewayAppId: mcpGatewayAppId
    apimPublisherEmail: apimPublisherEmail
    modelName: modelName
    modelVersion: modelVersion
    modelSkuName: modelSkuName
    modelCapacity: modelCapacity
    supportTokensPerMinute: supportTokensPerMinute
    docsTokensPerMinute: docsTokensPerMinute
    alertEmail: alertEmail
    enableAppGateway: enableAppGateway
    appGatewayHostName: appGatewayHostName
    appGatewayCertificateUri: appGatewayCertificateUri
  }
}

output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.containerRegistryEndpoint
output AZURE_CONTAINER_REGISTRY_NAME string = resources.outputs.containerRegistryName
output APIM_NAME string = resources.outputs.apimName
output APIM_GATEWAY_URL string = resources.outputs.apimGatewayUrl
output FOUNDRY_ACCOUNT_NAME string = resources.outputs.foundryAccountName
output FOUNDRY_PROJECT_ENDPOINT_SUPPORT string = resources.outputs.projectEndpoints.support
output FOUNDRY_PROJECT_ENDPOINT_DOCS string = resources.outputs.projectEndpoints.docs
output FOUNDRY_PROJECT_ENDPOINT_CUSTOPS string = resources.outputs.projectEndpoints.custops
output MODEL_DEPLOYMENT_NAME string = resources.outputs.modelDeploymentName
output MCP_GATEWAY_APP_ID string = mcpGatewayAppId
output LOG_ANALYTICS_WORKSPACE_ID string = resources.outputs.logAnalyticsCustomerId
output APPLICATIONINSIGHTS_NAME string = resources.outputs.appInsightsName
