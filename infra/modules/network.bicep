// Network: one VNet, one NSG per subnet, a Standard NAT gateway for egress and
// the Private DNS zone for Key Vault.
//
// New subnets are created with default outbound access disabled, so every subnet
// that needs internet egress (Container Apps pulling images, API Management
// calling Foundry and Content Safety) goes through the NAT gateway.
// Container Apps does not support the StandardV2 NAT gateway SKU; Standard is used.
// https://learn.microsoft.com/azure/container-apps/custom-virtual-networks

param location string
param tags object
param resourceToken string

var vnetName = 'vnet-ig26-${resourceToken}'

resource natPip 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: 'pip-ig26-nat-${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
    publicIPAddressVersion: 'IPv4'
  }
}

resource nat 'Microsoft.Network/natGateways@2024-05-01' = {
  name: 'ng-ig26-${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'Standard'
  }
  properties: {
    idleTimeoutInMinutes: 4
    publicIpAddresses: [
      {
        id: natPip.id
      }
    ]
  }
}

resource nsgAppGw 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-ig26-appgw'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Allow-GatewayManager'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: 'GatewayManager'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '65200-65535'
        }
      }
      {
        name: 'Allow-AzureLoadBalancer'
        properties: {
          priority: 110
          direction: 'Inbound'
          access: 'Allow'
          protocol: '*'
          sourceAddressPrefix: 'AzureLoadBalancer'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
      {
        name: 'Allow-HTTPS-Inbound'
        properties: {
          priority: 120
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: 'Internet'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '443'
        }
      }
    ]
  }
}

resource nsgInfra 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-ig26-infra'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        // Only the VNet (API Management, Application Gateway) may reach the internal environment.
        name: 'Allow-VNet-HTTPS'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourceAddressPrefix: 'VirtualNetwork'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRanges: ['80', '443']
        }
      }
    ]
  }
}

resource nsgApim 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-ig26-apim'
  location: location
  tags: tags
  properties: {
    securityRules: []
  }
}

resource nsgBackend 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: 'nsg-ig26-backend'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'Deny-Internet-Inbound'
        properties: {
          priority: 4000
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourceAddressPrefix: 'Internet'
          sourcePortRange: '*'
          destinationAddressPrefix: '*'
          destinationPortRange: '*'
        }
      }
    ]
  }
}

resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: ['10.42.0.0/16']
    }
    subnets: [
      {
        name: 'snet-appgw'
        properties: {
          addressPrefix: '10.42.0.0/24'
          networkSecurityGroup: { id: nsgAppGw.id }
          defaultOutboundAccess: false
        }
      }
      {
        // Container Apps workload profiles environment. /23 leaves room to scale.
        name: 'snet-infra'
        properties: {
          addressPrefix: '10.42.2.0/23'
          networkSecurityGroup: { id: nsgInfra.id }
          natGateway: { id: nat.id }
          defaultOutboundAccess: false
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: { serviceName: 'Microsoft.App/environments' }
            }
          ]
        }
      }
      {
        // API Management Standard v2 outbound VNet integration.
        // https://learn.microsoft.com/azure/api-management/integrate-vnet-outbound
        name: 'snet-apim'
        properties: {
          addressPrefix: '10.42.4.0/27'
          networkSecurityGroup: { id: nsgApim.id }
          natGateway: { id: nat.id }
          defaultOutboundAccess: false
          delegations: [
            {
              name: 'Microsoft.Web.serverFarms'
              properties: { serviceName: 'Microsoft.Web/serverFarms' }
            }
          ]
        }
      }
      {
        // Private endpoints.
        name: 'snet-backend'
        properties: {
          addressPrefix: '10.42.5.0/24'
          networkSecurityGroup: { id: nsgBackend.id }
          defaultOutboundAccess: false
          privateEndpointNetworkPolicies: 'Enabled'
        }
      }
    ]
  }
}

resource kvDns 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  #disable-next-line no-hardcoded-env-urls
  name: 'privatelink.vaultcore.azure.net'
  location: 'global'
  tags: tags
}

resource kvDnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: kvDns
  name: 'link-${vnetName}'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: { id: vnet.id }
  }
}

output vnetId string = vnet.id
output appGatewaySubnetId string = vnet.properties.subnets[0].id
output containerAppsSubnetId string = vnet.properties.subnets[1].id
output apimSubnetId string = vnet.properties.subnets[2].id
output backendSubnetId string = vnet.properties.subnets[3].id
output keyVaultPrivateDnsZoneId string = kvDns.id
output natPublicIp string = natPip.properties.ipAddress
