// Log Analytics, workspace-based Application Insights, optional action group.
//
// Application Insights keeps local authentication enabled because the Foundry
// tracing connection and the API Management logger use the connection string,
// which is the pattern in Microsoft's Foundry samples. The connection string is
// an ingestion endpoint identifier, not a read credential; query access still
// needs Entra RBAC on the workspace.

param location string
param tags object
param resourceToken string
param alertEmail string

resource law 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-ig26-${resourceToken}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-ig26-${resourceToken}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: law.id
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = if (!empty(alertEmail)) {
  name: 'ag-ig26-${resourceToken}'
  location: 'global'
  tags: tags
  properties: {
    groupShortName: 'ig26'
    enabled: true
    emailReceivers: [
      {
        name: 'lab-owner'
        emailAddress: alertEmail
        useCommonAlertSchema: true
      }
    ]
  }
}

output logAnalyticsWorkspaceId string = law.id
output logAnalyticsCustomerId string = law.properties.customerId
output appInsightsId string = appInsights.id
output appInsightsName string = appInsights.name
output actionGroupId string = empty(alertEmail) ? '' : actionGroup.id
