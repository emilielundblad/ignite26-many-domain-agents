# Troubleshooting

## `azd up` fails fast with `missing required inputs: mcpGatewayAppId`

In a terminal without interactive prompts (CI, agents, redirected output), recent azd versions validate required parameters before the preprovision hook has a chance to create the gateway app and set `MCP_GATEWAY_APP_ID`. Run the hook once by hand, then deploy:

```bash
python scripts/hooks.py preprovision
azd up
```

The hook is idempotent: it reuses the app on later runs.

## `azd up` stops in the preprovision hook with HTTP 403

Your account cannot register applications. Ask an admin to create the gateway app as described in [identity/README.md](../identity/README.md#if-you-cannot-create-the-app-yourself), then:

```bash
azd env set MCP_GATEWAY_APP_ID <appId>
azd env set MCP_GATEWAY_SP_ID <service principal object id>
azd env set IG26_SKIP_ENTRA_SETUP true
azd up
```

## Provisioning fails on the model deployment (quota or model not available)

Pick a model and version available as GlobalStandard in your region, or another region:

```bash
azd env set MODEL_NAME gpt-4.1-mini
azd env set MODEL_VERSION 2025-04-14
azd env set MODEL_CAPACITY 30
```

## Provisioning fails with a soft-deleted name conflict

A previous run left a soft-deleted API Management, Foundry or Key Vault with the same name. Run `python scripts/teardown.py` for the old environment, or create a new azd environment name.

## The postdeploy hook says app roles could not be assigned

Your account can register apps but not assign app roles to service principals. An admin with Cloud Application Administrator runs, for each agent identity printed by the hook:

```bash
python -m identity.assign_agent_roles --principal <agent identity object id> --role Support.Tools
python -m identity.assign_agent_roles --principal <agent identity object id> --role Docs.Tools
```

## Every tool call is denied, including Support tools

New app role assignments reach new tokens after a few minutes, and Foundry may cache a token. Wait five minutes and run the demo again. Check with `python -m identity.show_agent_identities` that the roles are there.

## Tool calls fail with 401 from the REST API scope

The MCP server policy validates the agent token and passes it on in `x-ig26-agent-token`, and the REST API policy validates it again. If your API Management version does not forward that header to tool operations, tool calls fail with 401 from `rest-*` APIs. Check the App Insights `requests` table. As a workaround set the named value `ig26-rest-scope-auth` to `off` in API Management > Named values. The MCP server scope still enforces the domain check; the REST paths then rely on API Management network placement only, so open an issue so we can track it.

## The setup script says the model route through API Management failed

The agents use their models through API Management (`ig26-models/<deployment>`). If that route fails, the script recreates the agents with the direct deployment so the tool demos still work, and demo 3 skips the token budget test. Common causes:

- the API Management managed identity role on Foundry is still propagating: wait ten minutes and run `python -m agents.setup_agents` again
- the project managed identity token is rejected: check `traces` in Application Insights for `DENY model route`

Set `IG26_REQUIRE_MODEL_GATEWAY=true` to make this a hard failure instead.

## The model does not call the credit-note tool

Language models do not always call a tool. Run demo 2 again. The gateway decision is independent of the model: you can see it in `traces` for any call to `mcp-custops-creditnotes`.

## Demo 3 does not hit the Support token limit

Raise the burst with `python -m agents.run_demo3 --burst 10`, or lower the budget with `azd env set SUPPORT_TOKENS_PER_MINUTE 2000` and `azd provision`.
