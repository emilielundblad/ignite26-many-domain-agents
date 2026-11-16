// OPTIONAL: identity for the GitHub Actions deploy workflow (.github/workflows/deploy.yml).
// You deploy this once, from your own session, because it creates role assignments:
//
//   az deployment sub create --location <region> --template-file infra/bootstrap/deploy-identity.bicep \
//     --parameters environmentName=<env> githubOidcSubject='<subject>'
//
// What it grants, and nothing more:
//   - a user-assigned managed identity with ONE federated credential for your repo's
//     `demo` environment (no client secret exists anywhere)
//   - Contributor on the lab resource group only
//   - Role Based Access Control Administrator on the lab resource group only, with a
//     condition: it may assign or remove only the five built-in roles the template
//     uses, and only to service principals (never to users or groups, never Owner)
//   - a custom role at subscription scope that can run deployments and nothing else,
//     because main.bicep is a subscription-scope deployment
//
// githubOidcSubject: GitHub repos created after 15 July 2026 use immutable,
// ID-based subject claims. Read your repo's exact subject with
//   gh api repos/<owner>/<repo>/actions/oidc/customization/sub
// and the GitHub doc "About security hardening with OpenID Connect", then pass
// the subject for environment `demo`.
targetScope = 'subscription'

param environmentName string
param location string = deployment().location
@description('Exact OIDC subject claim for the repo\'s `demo` environment.')
param githubOidcSubject string

var rgName = 'rg-ig26-${environmentName}'
var allowedRoleIds = [
  '7f951dda-4ed3-4680-a7ca-43fe172d538d' // AcrPull
  '53ca6127-db72-4b80-b1b0-d745d6d5456d' // Foundry User (Azure AI User)
  'a97b65f3-24c7-4388-baec-2e87135dc908' // Cognitive Services User
  '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
  '4633458b-17de-408a-b874-0445c86b69e6' // Key Vault Secrets User (App Gateway option)
]
var roleList = join(allowedRoleIds, ', ')
var rbacCondition = '((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/write\'})) OR (@Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleList}} AND @Request[Microsoft.Authorization/roleAssignments:PrincipalType] ForAnyOfAnyValues:StringEqualsIgnoreCase {\'ServicePrincipal\'})) AND ((!(ActionMatches{\'Microsoft.Authorization/roleAssignments/delete\'})) OR (@Resource[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {${roleList}} AND @Resource[Microsoft.Authorization/roleAssignments:PrincipalType] ForAnyOfAnyValues:StringEqualsIgnoreCase {\'ServicePrincipal\'}))'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: rgName
  location: location
  tags: {
    event: 'ignite2026'
    'azd-env-name': environmentName
  }
}

resource deployerRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(subscription().id, 'ig26-subscription-deployer')
  properties: {
    roleName: 'ig26 subscription deployer (${subscription().subscriptionId})'
    description: 'Run subscription-scope ARM deployments and read resource groups. Nothing else.'
    type: 'CustomRole'
    assignableScopes: [subscription().id]
    permissions: [
      {
        actions: [
          'Microsoft.Resources/deployments/*'
          'Microsoft.Resources/subscriptions/resourceGroups/read'
          'Microsoft.Resources/subscriptions/read'
        ]
        notActions: []
      }
    ]
  }
}

module identity 'deploy-identity-rg.bicep' = {
  name: 'ig26-deploy-identity'
  scope: rg
  params: {
    location: location
    githubOidcSubject: githubOidcSubject
    rbacCondition: rbacCondition
  }
}

resource deployerAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, 'ig26-deployer', environmentName)
  properties: {
    principalId: identity.outputs.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: deployerRole.id
  }
}

output AZURE_CLIENT_ID string = identity.outputs.clientId
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_SUBSCRIPTION_ID string = subscription().subscriptionId
