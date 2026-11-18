# identity

Entra pieces of the pattern. All scripts use your own signed-in session (`azd auth login`, falling back to `az login`) and the Microsoft Graph v1.0 API. They never print tokens.

| Script | What it does | Writes to Entra |
|---|---|---|
| `setup_gateway_app.py` | Creates or reuses the app `ig26-mcp-gateway-<env>`: identifier URI `api://<appId>`, v2 tokens, app roles `Support.Tools`, `Docs.Tools`, `CustOps.Tools` (applications only), service principal with *assignment required*. Runs as the azd `preprovision` hook | Yes |
| `setup_gateway_app.ps1` | PowerShell 7 twin of the above (Microsoft Graph PowerShell SDK), for showing the Entra creation steps on screen in demo 1. Same deterministic role IDs; the two scripts can be mixed freely | Yes |
| `assign_agent_roles.py` | Grants or revokes an app role for an agent identity. Called by `agents/setup_agents.py` | Yes |
| `tag_agents.py` | Sets the custom security attribute `AgentAttributes.AgentApprovalStatus = Gateway_Approved` on the lab agent identities, for the report-only policy `ig26-block-unapproved-agents` (demo 1). `--revoke` clears it | Yes |
| `run_demo1.py` | Demo 1, read-only: walks the five slide steps, pauses between them, masks IDs for recording, checks Conditional Access is report-only. See [docs/demo-1-runbook.md](../docs/demo-1-runbook.md) | No |
| `show_agent_identities.py` | Short read-only report: identity, blueprint, sponsors, gateway roles | No |

## Permissions you need

- Register an application: allowed for members by default, otherwise the **Application Developer** role.
- Assign app roles to service principals: as owner of the app the script creates, or with **Cloud Application Administrator**.
- Read agent identities and sponsors: any member can read service principals; reading sponsors may need **Agent ID Administrator** or a reader role, otherwise the report says so and continues.

Activate admin roles just in time with Privileged Identity Management, and only for the run.

## If you cannot create the app yourself

An admin creates it once:

1. Entra admin center > App registrations > New registration: name `ig26-mcp-gateway-<env>`, single tenant, no redirect URI.
2. Expose an API > Application ID URI: accept `api://<appId>`.
3. Manifest: set `"requestedAccessTokenVersion": 2` under `api`.
4. App roles > create three roles, *Allowed member types: Applications*, values `Support.Tools`, `Docs.Tools`, `CustOps.Tools`.
5. Enterprise applications > the app > Properties > *Assignment required?* Yes.
6. Give you the application (client) ID and the enterprise application object ID, then you run:
   ```bash
   azd env set MCP_GATEWAY_APP_ID <appId>
   azd env set MCP_GATEWAY_SP_ID <object id>
   azd env set IG26_SKIP_ENTRA_SETUP true
   ```

The role IDs that the scripts expect are generated deterministically from the role values. If an admin created the roles by hand with other IDs, `assign_agent_roles.py` will not find them; in that case let the admin run `python -m identity.setup_gateway_app` instead, which reuses the app by name and adds what is missing.

## What stays in the portal on purpose

Sponsors (the Graph API accepts application permissions only), Conditional Access policies and policy plans (kept in report-only, switched on by you), and lifecycle policies. The steps are in [docs/demo-walkthrough.md](../docs/demo-walkthrough.md#demo-1-per-domain-identities).
