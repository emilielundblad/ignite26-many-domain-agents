"""Read-only report for Demo 1: each lab agent's Entra identity, its blueprint,
sponsors and the gateway app roles it holds. Changes nothing.

    python -m identity.show_agent_identities
"""

from __future__ import annotations

import json
from pathlib import Path

from identity import graph
from identity.azd_env import get_values, require
from identity.setup_gateway_app import APP_ROLES, role_id

STATE = Path(__file__).resolve().parent.parent / ".ig26" / "agents.json"


def main() -> None:
    (sp_id,) = require(get_values(), "MCP_GATEWAY_SP_ID")
    if not STATE.exists():
        raise SystemExit("No agents yet. Run `azd up` (or python -m agents.setup_agents) first.")
    agents = json.loads(STATE.read_text())["agents"]
    names = {role_id(v): v for v, _, _ in APP_ROLES}
    for a in agents:
        pid = a["instanceIdentity"]["principalId"]
        print(f"\n{a['name']}  (project: {a['project']})")
        try:
            sp = graph.request("GET", f"/servicePrincipals/{pid}")
        except graph.GraphError as exc:
            print(f"  could not read identity {pid}: {exc}")
            continue
        print(f"  object type     : {sp.get('@odata.type', 'servicePrincipal')}")
        print(f"  display name    : {sp.get('displayName')}")
        print(f"  object id       : {pid}")
        print(f"  client id       : {sp.get('appId')}")
        print(f"  blueprint appId : {sp.get('agentIdentityBlueprintId', 'n/a')}")
        try:
            sponsors = graph.request("GET", f"/servicePrincipals/{pid}/microsoft.graph.agentIdentity/sponsors?$select=id,displayName")
            print(f"  sponsors        : {', '.join(s.get('displayName', s['id']) for s in sponsors.get('value', [])) or 'none (add one in the Entra admin center)'}")
        except graph.GraphError as exc:
            print(f"  sponsors        : not readable ({exc.code or exc.status})")
        found = graph.request("GET", f"/servicePrincipals/{pid}/appRoleAssignments")
        roles = [names.get(x["appRoleId"], x["appRoleId"]) for x in found.get("value", []) if x["resourceId"] == sp_id]
        print(f"  gateway roles   : {', '.join(roles) or 'none'}")


if __name__ == "__main__":
    main()
