// OPTIONAL (enableAppGateway = true): Application Gateway WAF_v2 in front of the
// API Management gateway, WAF policy in Prevention mode, certificate from Key
// Vault by versionless secret ID through a user-assigned identity.
// Needs your own domain and certificate, so it is off by default.
//
// Before enabling: import the PFX into the Key Vault (it has no public network
// access, so do it from a VNet-connected machine or temporarily allow your IP),
// then pass its versionless secret URI as appGatewayCertificateUri.

param location string
param tags object
param resourceToken string
param subnetId string
param hostName string
param certificateUri string
param keyVaultName string
param apimGatewayHostName string
param logAnalyticsWorkspaceId string
param actionGroupId string

@description('Default Rule Set version. Check which versions your region offers.')
param wafRuleSetVersion string = '2.1'

var keyVaultSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'
var name = 'agw-ig26-${resourceToken}'

resource kv 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: keyVaultName
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-ig26-agw-${resourceToken}'
  location: location
  tags: tags
}

resource kvSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(kv.id, identity.id, keyVaultSecretsUserRoleId)
  scope: kv
  properties: {
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', keyVaultSecretsUserRoleId)
  }
}

resource pip 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: 'pip-${name}'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  zones: ['1', '2', '3']
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource waf 'Microsoft.Network/ApplicationGatewayWebApplicationFirewallPolicies@2024-05-01' = {
  name: 'waf-ig26-${resourceToken}'
  location: location
  tags: tags
  properties: {
    policySettings: {
      state: 'Enabled'
      mode: 'Prevention'
      requestBodyCheck: true
      maxRequestBodySizeInKb: 128
      fileUploadLimitInMb: 10
    }
    managedRules: {
      managedRuleSets: [
        {
          ruleSetType: 'Microsoft_DefaultRuleSet'
          ruleSetVersion: wafRuleSetVersion
        }
        {
          ruleSetType: 'Microsoft_BotManagerRuleSet'
          ruleSetVersion: '1.1'
        }
      ]
    }
  }
}

resource agw 'Microsoft.Network/applicationGateways@2024-05-01' = {
  name: name
  location: location
  tags: tags
  zones: ['1', '2', '3']
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    sku: {
      name: 'WAF_v2'
      tier: 'WAF_v2'
    }
    autoscaleConfiguration: {
      minCapacity: 1
      maxCapacity: 2
    }
    firewallPolicy: {
      id: waf.id
    }
    sslPolicy: {
      policyType: 'Predefined'
      policyName: 'AppGwSslPolicy20220101S'
    }
    gatewayIPConfigurations: [
      {
        name: 'gwip'
        properties: { subnet: { id: subnetId } }
      }
    ]
    frontendIPConfigurations: [
      {
        name: 'public'
        properties: { publicIPAddress: { id: pip.id } }
      }
    ]
    frontendPorts: [
      {
        name: 'https'
        properties: { port: 443 }
      }
    ]
    sslCertificates: [
      {
        name: 'listener-cert'
        properties: { keyVaultSecretId: certificateUri }
      }
    ]
    backendAddressPools: [
      {
        name: 'apim'
        properties: { backendAddresses: [ { fqdn: apimGatewayHostName } ] }
      }
    ]
    probes: [
      {
        name: 'apim-status'
        properties: {
          protocol: 'Https'
          path: '/status-0123456789abcdef'
          interval: 30
          timeout: 30
          unhealthyThreshold: 3
          pickHostNameFromBackendHttpSettings: true
          match: { statusCodes: ['200-399'] }
        }
      }
    ]
    backendHttpSettingsCollection: [
      {
        name: 'apim-https'
        properties: {
          port: 443
          protocol: 'Https'
          pickHostNameFromBackendAddress: true
          requestTimeout: 230
          probe: { id: resourceId('Microsoft.Network/applicationGateways/probes', name, 'apim-status') }
        }
      }
    ]
    httpListeners: [
      {
        name: 'https'
        properties: {
          frontendIPConfiguration: { id: resourceId('Microsoft.Network/applicationGateways/frontendIPConfigurations', name, 'public') }
          frontendPort: { id: resourceId('Microsoft.Network/applicationGateways/frontendPorts', name, 'https') }
          protocol: 'Https'
          hostName: hostName
          requireServerNameIndication: true
          sslCertificate: { id: resourceId('Microsoft.Network/applicationGateways/sslCertificates', name, 'listener-cert') }
        }
      }
    ]
    requestRoutingRules: [
      {
        name: 'to-apim'
        properties: {
          ruleType: 'Basic'
          priority: 100
          httpListener: { id: resourceId('Microsoft.Network/applicationGateways/httpListeners', name, 'https') }
          backendAddressPool: { id: resourceId('Microsoft.Network/applicationGateways/backendAddressPools', name, 'apim') }
          backendHttpSettings: { id: resourceId('Microsoft.Network/applicationGateways/backendHttpSettingsCollection', name, 'apim-https') }
        }
      }
    ]
    // Response buffering off so agent responses can stream.
    globalConfiguration: {
      enableRequestBuffering: true
      enableResponseBuffering: false
    }
  }
  dependsOn: [
    kvSecretsUser
  ]
}

resource diag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: agw
  properties: {
    workspaceId: logAnalyticsWorkspaceId
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
  }
}

resource backendHealth 'Microsoft.Insights/metricAlerts@2018-03-01' = if (!empty(actionGroupId)) {
  name: 'alert-ig26-agw-unhealthy'
  location: 'global'
  tags: tags
  properties: {
    description: 'Application Gateway has unhealthy backend hosts.'
    severity: 2
    enabled: true
    scopes: [agw.id]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'unhealthy'
          criterionType: 'StaticThresholdCriterion'
          metricName: 'UnhealthyHostCount'
          metricNamespace: 'Microsoft.Network/applicationGateways'
          operator: 'GreaterThan'
          threshold: 0
          timeAggregation: 'Average'
        }
      ]
    }
    actions: [
      {
        actionGroupId: actionGroupId
      }
    ]
  }
}

output publicIp string = pip.properties.ipAddress
