# Step 1: Foundation infrastructure (Claude Code)

> **Note:** the code these prompts produce is already in this repository. Use the prompt to rebuild a step from scratch, to extend it, or to show on stage how it was built.

---

Read CLAUDE.md first and follow it. Use the deploy identity and workflow from step 0.

Goal: deploy the shared platform from the architecture in CLAUDE.md with Bicep, so that steps 3 to 5 have somewhere to run.

Build, as Bicep modules (prefer Azure Verified Modules), in this order:

1. Network: VNet `vnet-ig26` with subnets `snet-appgw`, `snet-infra`, `snet-domains`, `snet-apim`, `snet-backend`, each with its own NSG. Delegate Container Apps subnets to `Microsoft.App/environments` (workload profiles, /27 or larger) and the APIM subnet to `Microsoft.Web/serverFarms`. Avoid the Container Apps reserved ranges listed on Learn. Two NAT gateways on the Standard SKU with static public IPs: one for infra and backend, one for domains. Read the Container Apps custom VNet page and confirm StandardV2 is still unsupported before you choose.
2. Monitoring: Log Analytics workspace, workspace-based Application Insights with local auth disabled, an action group sending email to <alert email>, one alert: Application Gateway backend health below 100 percent.
3. Data: Key Vault (RBAC, purge protection, public access disabled, private endpoint), Container Registry (Standard or Premium, admin user disabled), PostgreSQL Flexible Server with Entra-only authentication (password auth explicitly disabled, an Entra group as admin, private access), and the Private DNS zones these need, linked to the VNet.
4. Runtime: Container Apps environment, workload profiles, internal only, in `snet-infra`. Private DNS zone for its default domain with `*` and `@` A records to its static IP, linked to the VNet so Application Gateway can resolve it.
5. AI gateway: API Management Standard v2 with VNet integration for outbound on `snet-apim`, public endpoint, system-assigned identity, App Insights logger. Read the APIM v2 tiers page and confirm MCP servers and the llm policies are supported on Standard v2.
6. Ingress: Application Gateway WAF_v2 with a WAF policy in Prevention mode on DRS 2.2, listener for `admin.ig26.<your-domain>` and `*.ig26.<your-domain>`, certificate from Key Vault by versionless secret ID through a user-assigned identity with Key Vault Secrets User. Response buffering off so agent responses can stream. I will upload the certificate to Key Vault myself.
7. Foundry: a Foundry account with model deployments <model names, region>, and three projects: `support`, `docs`, `custops`. Tracing connected to Application Insights.

CHECKPOINTS:
- Before writing code: list every resource, SKU, region and role assignment, plus an estimated monthly cost.
- Before each deployment: the what-if summary.
- After deployment: a short `docs/demo-state.md` update with resource names and endpoints.

Acceptance: `az resource list -g rg-ig26-...` shows everything tagged `event=ignite2026`; Application Gateway backend health is healthy for a hello-world Container App; APIM can reach that app over the VNet.
