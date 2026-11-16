# infra

Bicep for the whole lab. `azd provision` deploys `main.bicep` at subscription scope; it creates `rg-ig26-<env>` and calls `resources.bicep`.

| File | What |
|---|---|
| `main.bicep`, `main.parameters.json` | Entry point and azd parameter mapping |
| `resources.bicep` | The domain table and the wiring between modules |
| `modules/network.bicep` | VNet, NSGs, NAT gateway, Key Vault Private DNS |
| `modules/monitoring.bicep`, `modules/alerts.bicep` | Log Analytics, Application Insights, action group, gateway alert |
| `modules/keyvault.bicep` | Key Vault with private endpoint |
| `modules/registry.bicep` | Container Registry |
| `modules/container-apps.bicep`, `modules/container-apps-dns.bicep` | Internal environment, Private DNS, the three apps |
| `modules/content-safety.bicep` | Content Safety, keys disabled |
| `modules/foundry.bicep` | Foundry account, model deployment, projects, tracing connection |
| `modules/foundry-connections.bicep` | Project connections: model route and MCP servers |
| `modules/apim.bicep` | API Management, logger, diagnostics, named values, backends, policy fragment |
| `modules/apim-domain.bicep` | Per domain: REST API, MCP server, product, policies |
| `modules/apim-models.bicep` | Per domain: model route with content safety, token limit, token metrics |
| `modules/roles.bicep` | API Management data-plane roles |
| `modules/app-gateway.bicep` | Optional WAF_v2 |
| `policies/*.xml` | API Management policies |
| `bootstrap/` | Optional GitHub Actions deploy identity |

Preview the changes before every deployment:

```bash
azd provision --preview
```

Settings you can change with `azd env set`: `MODEL_NAME`, `MODEL_VERSION`, `MODEL_CAPACITY`, `SUPPORT_TOKENS_PER_MINUTE`, `DOCS_TOKENS_PER_MINUTE`, `ALERT_EMAIL`, `APIM_PUBLISHER_EMAIL`, `OWNER_TAG`, `ENABLE_APP_GATEWAY`, `APP_GATEWAY_HOST_NAME`, `APP_GATEWAY_CERT_URI`.

## Optional Application Gateway certificate

`ENABLE_APP_GATEWAY=true` needs a domain you own and a TLS certificate for `APP_GATEWAY_HOST_NAME`. Import the certificate (PFX) into the deployed Key Vault — for example `az keyvault certificate import --vault-name <vault> --name appgw-cert --file cert.pfx`. The vault has no public network access, so run the import from a VNet-connected machine or temporarily allow your IP. Then set `APP_GATEWAY_CERT_URI` to the certificate's **versionless** secret URI (`https://<vault>.vault.azure.net/secrets/appgw-cert`) and run `azd provision` again. The Application Gateway's user-assigned identity is granted Key Vault Secrets User by the template.
