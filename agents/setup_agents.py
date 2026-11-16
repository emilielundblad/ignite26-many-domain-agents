"""Create the Support and Documentation agents and grant their identities their
domain's app roles. Runs as the azd `postdeploy` hook; safe to re-run.

For each agent:
1. Create a new agent version in its domain project (Foundry Agent Service).
   Model:  ig26-models-<project>/<deployment>, i.e. through the domain's AI gateway route.
   Tools:  MCP servers in API Management, through project connections that
           authenticate as the agent's own Entra agent identity.
2. Wait for Foundry to create the agent identity and read its object ID.
3. Grant that identity the domain app role(s) on the MCP gateway app.
4. Smoke test: one short question. If the model route through API Management
   fails, fall back to the direct deployment (unless IG26_REQUIRE_MODEL_GATEWAY=true)
   and say so loudly. Tool calls always go through API Management.

No agent is created for Customer operations: that domain exists but is not enabled.

https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity
https://learn.microsoft.com/azure/foundry/agents/how-to/mcp-authentication
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime, timezone

from azure.ai.projects.models import MCPTool, PromptAgentDefinition

from agents.common import AGENTS, SERVER_LABELS, AgentSpec, ask, env, project_client, save_state
from identity import graph
from identity.assign_agent_roles import assign


def build_definition(spec: AgentSpec, model: str, gateway_url: str) -> PromptAgentDefinition:
    tools = [
        MCPTool(
            server_label=SERVER_LABELS[server],
            server_url=f"{gateway_url}/{server}/mcp",
            # Connection names are unique per account, so they carry the project suffix.
            project_connection_id=f"{server}-{spec.project}",
            require_approval="never",
        )
        for server in spec.mcp_servers
    ]
    return PromptAgentDefinition(model=model, instructions=spec.instructions, tools=tools)


def wait_for_identity(client, name: str, timeout: int = 300) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        details = client.agents.get(name)
        ident = getattr(details, "instance_identity", None)
        if ident and getattr(ident, "principal_id", None):
            blueprint = getattr(details, "blueprint", None)
            return {
                "instanceIdentity": {"principalId": ident.principal_id, "clientId": ident.client_id},
                "blueprint": {"principalId": blueprint.principal_id, "clientId": blueprint.client_id} if blueprint else None,
            }
        time.sleep(10)
    raise SystemExit(f"Foundry did not report an agent identity for {name} within {timeout} seconds. Re-run `python -m agents.setup_agents`.")


def create(client, spec: AgentSpec, model: str, gateway_url: str):
    return client.agents.create_version(
        spec.name,
        definition=build_definition(spec, model, gateway_url),
        description=spec.description,
        metadata={**spec.metadata, "model_route": "gateway" if "/" in model else "direct"},
    )


def main() -> None:
    values = env()
    gateway_url = values["APIM_GATEWAY_URL"].rstrip("/")
    deployment = values["MODEL_DEPLOYMENT_NAME"]
    sp_id = values.get("MCP_GATEWAY_SP_ID")
    require_gateway = os.getenv("IG26_REQUIRE_MODEL_GATEWAY", "false").lower() == "true"

    state = {"createdAt": datetime.now(timezone.utc).isoformat(), "agents": []}
    problems = []

    for spec in AGENTS:
        gateway_model = f"ig26-models-{spec.project}/{deployment}"
        client = project_client(values[spec.endpoint_key])
        print(f"\n[{spec.name}] creating agent version in project '{spec.project}' (model route: AI gateway)")
        version = create(client, spec, gateway_model, gateway_url)
        ids = wait_for_identity(client, spec.name)
        principal = ids["instanceIdentity"]["principalId"]
        print(f"[{spec.name}] version {version.version}, agent identity {principal}")

        if sp_id:
            for role in spec.app_roles:
                try:
                    created = assign(sp_id, principal, role)
                    print(f"[{spec.name}] app role {role}: {'assigned' if created else 'already assigned'}")
                except graph.GraphError as exc:
                    problems.append(f"{spec.name}: could not assign {role} ({exc.status} {exc.code}). See identity/README.md.")
        else:
            problems.append("MCP_GATEWAY_SP_ID is not set; app roles were not assigned.")

        route = "gateway"
        try:
            ask(client, spec.name, "Reply with the single word READY.", retries=2, wait=15)
            print(f"[{spec.name}] smoke test passed through the AI gateway model route")
        except Exception as exc:  # noqa: BLE001
            msg = str(exc).splitlines()[0][:300]
            if require_gateway:
                problems.append(f"{spec.name}: model route through API Management failed: {msg}")
            else:
                print(f"[{spec.name}] WARNING: model route through API Management failed ({msg}).")
                print(f"[{spec.name}] Falling back to the direct deployment so the tool demos still work. See docs/troubleshooting.md.")
                version = create(client, spec, deployment, gateway_url)
                route = "direct"

        state["agents"].append(
            {
                "name": spec.name,
                "project": spec.project,
                "endpointKey": spec.endpoint_key,
                "version": version.version,
                "modelRoute": route,
                "appRoles": list(spec.app_roles),
                **ids,
            }
        )

    save_state(state)
    print("\nAgent state written to .ig26/agents.json (git-ignored).")
    print("App role changes can take a few minutes to reach new tokens. Then run: python -m agents.run_demo2")
    if problems:
        print("\nAction needed:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)


if __name__ == "__main__":
    main()
