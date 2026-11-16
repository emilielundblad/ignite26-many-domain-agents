# agents

Agent setup and demo scripts for Foundry Agent Service, using `azure-ai-projects` 2.x and your own signed-in identity.

| Script | What |
|---|---|
| `setup_agents.py` | Creates `support-agent` (project `support`) and `docs-agent` (project `docs`), waits for their agent identities, grants the gateway app roles, smoke-tests the model route. Runs as the azd `postdeploy` hook |
| `run_demo2.py` | Demo 2: trace one request, the boundary test, tool output as data |
| `run_demo3.py` | Demo 3: no token, content safety, token budgets, token metrics |
| `common.py` | Agent definitions, instructions and helpers |

Agents use models through `ig26-models/<deployment>` (the domain's route in API Management) and tools through MCP servers in API Management. No agent exists for Customer operations; `support-agent` is configured with the Customer ops MCP server on purpose so the gateway can deny it.

State about the created agents (names, versions, identity IDs) is written to `.ig26/agents.json`, which is git-ignored.

## Prerequisites for running the demos

`azd up` prepares everything: the `postdeploy` hook creates `.venv` from the hash-pinned `requirements.txt` and runs `setup_agents.py`. The scripts read these values from the azd environment (or the process environment):

| Value | Needed by | Where it comes from |
|---|---|---|
| `APIM_GATEWAY_URL` | setup, demo 2, demo 3 | Bicep output, set by `azd up` |
| `MODEL_DEPLOYMENT_NAME` | setup, demo 2, demo 3 | Bicep output, set by `azd up` |
| `FOUNDRY_PROJECT_ENDPOINT_SUPPORT` / `FOUNDRY_PROJECT_ENDPOINT_DOCS` | setup, demo 2, demo 3 | Bicep outputs, set by `azd up` |
| `MCP_GATEWAY_APP_ID`, `MCP_GATEWAY_SP_ID` | setup only | `preprovision` hook (or set by hand, see [identity/README.md](../identity/README.md)) |
| `LOG_ANALYTICS_WORKSPACE_ID` | demo 3, optional | Bicep output; without it the token-metrics step is skipped |
| `.ig26/agents.json` | demo 2, demo 3 | Written by `setup_agents.py` |

You also need a signed-in `azd auth login` (or `az login`) session; the scripts authenticate with `AzureDeveloperCliCredential`, falling back to `AzureCliCredential`. If `azd up` finished but the agents are missing, run setup again with `.venv`'s Python: `python -m agents.setup_agents`.
