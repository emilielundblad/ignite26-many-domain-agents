# Security design and trade-offs

This lab follows the [Microsoft cloud security benchmark](https://learn.microsoft.com/security/benchmark/azure/overview) (MCSB) where a reproducible lab allows it. This page lists what is done, and where the lab deliberately stops short of production, so nobody copies a shortcut without knowing.

## Identity and access (MCSB IM, PA)

| Control | How |
|---|---|
| No shared keys | `disableLocalAuth` on Foundry and Content Safety; registry admin user off; Key Vault in RBAC mode |
| Workload identities | API Management system-assigned identity to Content Safety and Foundry; user-assigned identity for image pulls; Foundry agent identities for tool calls; project managed identity for the model route |
| No credentials on the gateway app | The Entra app only receives tokens. It has no secrets or certificates |
| Access as a reviewable object | App roles with *assignment required*; an agent without an assignment cannot get a token |
| Least privilege | Cognitive Services User on Content Safety, Cognitive Services OpenAI User on Foundry, AcrPull on the registry, Foundry User for the operator. Each on one resource |
| CI without secrets | GitHub OIDC to a user-assigned identity. RBAC Administrator is constrained by a condition to five named roles, assigned to service principals only |
| Human admin actions | Entra changes run from your own session. Sponsors and Conditional Access are portal steps, kept in report-only |

## Network (MCSB NS)

| Control | How |
|---|---|
| Private runtime | Container Apps environment is internal; apps reachable from the VNet only |
| Private secrets store | Key Vault public network access disabled, private endpoint, Private DNS |
| Segmentation | NSG on every subnet; default outbound access disabled; egress through a NAT gateway |
| TLS | TLS 1.0 and 1.1 disabled on the gateway, frontend and backend; HTTPS only on every API |
| Optional WAF | Application Gateway WAF_v2, Prevention mode, Default Rule Set and Bot Manager |

## AI-specific controls

| Control | How |
|---|---|
| Policy before the model | `validate-azure-ad-token`, agent marker check (`xms_act_fct` 11 or `xms_par_app_azp`, named value `ig26-agent-token-check`: audit by default), domain app role check on the `roles` claim only, `llm-content-safety` with Prompt Shields, `llm-token-limit` |
| Tool output is data | Agent instructions say so; ticket 1043 tests it; Prompt Shields checks tool arguments |
| Boundary in two places | MCP server scope and REST API scope both run the domain check |
| Auditability | Every allow and deny is a trace record with the caller's client ID; token metrics per domain |

## Logging (MCSB LT)

Diagnostic settings on API Management, Container Apps, Key Vault and the registry send logs to Log Analytics. API Management logs to Application Insights with W3C correlation and **no request or response bodies**, so prompts and tool payloads are not copied into logs.

## Supply chain (MCSB DS)

Python dependencies are pinned with hashes and installed with `--require-hashes`. GitHub Actions are pinned to full commit SHAs. Dependabot, CodeQL (`security-extended`) and dependency review run on the repo. Containers run as a non-root user with no build tools in the final image.

## Deliberate lab trade-offs

| Trade-off | Why | Production direction |
|---|---|---|
| Foundry and Content Safety have public endpoints (Entra-only) | Private Foundry Agent Service needs the standard agent setup with your own VNet and storage, which doubles the template | Foundry standard agent setup with private networking; private endpoints for Content Safety |
| API Management gateway is public | Foundry Agent Service must reach it | Application Gateway or Front Door with WAF in front, or private networking for both |
| Application Insights keeps local auth | Foundry tracing and the API Management logger use the connection string, as in Microsoft's samples | Entra-authenticated ingestion when both support it |
| Registry public network access | Standard SKU; azd remote build | Premium SKU with private endpoint and dedicated agent pool |
| Base images pinned by tag, not digest | Dependabot proposes digests after the first run | Pin by digest, sign images, scan in CI |
| Key Vault soft-delete retention 7 days | Lab cleanup | 90 days |
| One resource group | One-command deploy and teardown | Resource group or subscription per domain |
| No PostgreSQL | Not needed by the demos | See [Govern agent access to PostgreSQL with Entra Agent ID](https://learn.microsoft.com/entra/agent-id/govern-agent-access-azure-postgresql) |
