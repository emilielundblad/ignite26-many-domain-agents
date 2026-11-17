---
name: microsoft-graph
description: >
  Call the Microsoft Graph API for this lab: inspect or change the governed MCP
  gateway app, its app roles, agent identities (service principals), app role
  assignments, sponsors and Conditional Access state. Use for any Entra ID /
  Microsoft Graph question or operation in this repository.
---

# Microsoft Graph in this repository

## Preferred paths, in order

1. **Repo scripts** (idempotent, reviewed, no secrets) — always first choice for
   changes:
   - `python -m identity.setup_gateway_app` or `pwsh identity/setup_gateway_app.ps1`
     — create/reuse the gateway app `ig26-mcp-gateway-<env>`, app roles, service
     principal with assignment required.
   - `python -m identity.assign_agent_roles --principal <sp object id> --role
     Support.Tools|Docs.Tools|CustOps.Tools [--revoke]` — grant/revoke a domain.
   - `python -m identity.show_agent_identities` — read-only report.
2. **identity/graph.py helper** for ad-hoc Python: `graph.request("GET", "/...")`
   authenticates with the signed-in azd/az session (never prints tokens).
3. **Microsoft Graph MCP server** (`.vscode/mcp.json`, Lokka in client-token mode):
   start it, then supply a token from the signed-in CLI —
   `az account get-access-token --resource-type ms-graph --query accessToken -o tsv`
   — to its `set-access-token` tool. No client secret exists or may be created.
4. **Raw REST** via `az rest --resource-type ms-graph` or
   `Invoke-MgGraphRequest` (PowerShell 7 + Microsoft.Graph modules).

## Lab invariants (do not break)

- The gateway app has **no credentials** — never add a client secret or certificate.
- App role IDs are **deterministic UUIDv5** under namespace
  `6f1c3c63-0e4e-4f3f-9a54-6b7d1f2a2a26` with the role value as name; both the
  Python and PowerShell setup scripts must agree.
- `appRoleAssignmentRequired` stays **true** on the gateway service principal.
- Nobody is ever granted `CustOps.Tools` — demo 2's boundary test depends on it.
- Conditional Access policies stay in **report-only**; sponsors are set in the
  portal (Graph only accepts application permissions for sponsors).

## Useful queries

- Agent identities (service principals of Foundry agents):
  `GET /servicePrincipals?$filter=tags/any(t:t eq 'AgentIdentity')` — or look up
  the object IDs from `.ig26/agents.json`.
- Role assignments on the gateway:
  `GET /servicePrincipals/{MCP_GATEWAY_SP_ID}/appRoleAssignedTo`
- The gateway app: `GET /applications?$filter=displayName eq 'ig26-mcp-gateway-<env>'`

`MCP_GATEWAY_APP_ID` and `MCP_GATEWAY_SP_ID` come from `azd env get-values`.
