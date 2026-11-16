// Alerts on the AI gateway. Created only when an action group exists.

param tags object
param apimName string
param actionGroupId string

resource apim 'Microsoft.ApiManagement/service@2024-06-01-preview' existing = {
  name: apimName
}

resource gateway5xx 'Microsoft.Insights/metricAlerts@2018-03-01' = if (!empty(actionGroupId)) {
  name: 'alert-ig26-gateway-5xx'
  location: 'global'
  tags: tags
  properties: {
    description: 'API Management returned more than 10 server errors in 5 minutes.'
    severity: 2
    enabled: true
    scopes: [apim.id]
    evaluationFrequency: 'PT1M'
    windowSize: 'PT5M'
    criteria: {
      'odata.type': 'Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria'
      allOf: [
        {
          name: 'server-errors'
          criterionType: 'StaticThresholdCriterion'
          metricName: 'Requests'
          metricNamespace: 'Microsoft.ApiManagement/service'
          operator: 'GreaterThan'
          threshold: 10
          timeAggregation: 'Total'
          dimensions: [
            {
              name: 'GatewayResponseCodeCategory'
              operator: 'Include'
              values: ['5xx']
            }
          ]
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
