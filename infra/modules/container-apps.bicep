// Internal Container Apps environment (workload profiles) and the three mock
// line-of-business APIs. Nothing here has a public endpoint: the environment is
// internal, and API Management reaches it over the VNet through a Private DNS
// zone for the environment's default domain.
// https://learn.microsoft.com/azure/container-apps/networking

param location string
param tags object
param resourceToken string
param infrastructureSubnetId string
param vnetId string
param logAnalyticsWorkspaceId string
param registryName string
param registryLoginServer string

@description('Apps to create: name, serviceName (azd service), domain.')
param apps array

var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource registry 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: registryName
}

resource pullIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-ig26-acrpull-${resourceToken}'
  location: location
  tags: tags
}

resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registry.id, pullIdentity.id, acrPullRoleId)
  scope: registry
  properties: {
    principalId: pullIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-ig26-${resourceToken}'
  location: location
  tags: tags
  properties: {
    vnetConfiguration: {
      infrastructureSubnetId: infrastructureSubnetId
      internal: true
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
    // Logs go to Log Analytics through diagnostic settings, so no shared key is needed.
    appLogsConfiguration: {
      destination: 'azure-monitor'
    }
    zoneRedundant: false
  }
}

resource envDiag 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'to-log-analytics'
  scope: env
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

// The zone name is the environment's default domain, known only after the
// environment exists, so the zone lives in its own module.
module envDns 'container-apps-dns.bicep' = {
  name: 'container-apps-dns'
  params: {
    tags: tags
    zoneName: env.properties.defaultDomain
    staticIp: env.properties.staticIp
    vnetId: vnetId
  }
}

resource containerApps 'Microsoft.App/containerApps@2024-03-01' = [for app in apps: {
  name: app.name
  location: location
  // azd finds the app to deploy to by this tag.
  tags: union(tags, { 'azd-service-name': app.serviceName, domain: app.domain })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${pullIdentity.id}': {}
    }
  }
  properties: {
    environmentId: env.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        // "external" inside an internal environment means reachable from the VNet only.
        external: true
        targetPort: 8080
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registryLoginServer
          identity: pullIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          // Placeholder until `azd deploy` pushes the real image.
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'LOG_LEVEL'
              value: 'INFO'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
  dependsOn: [
    acrPull
  ]
}]

output defaultDomain string = env.properties.defaultDomain
output environmentName string = env.name
output staticIp string = env.properties.staticIp
