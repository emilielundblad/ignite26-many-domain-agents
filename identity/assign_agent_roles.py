"""Grant agent identities the app roles of their domain on the MCP gateway app.

An app role assignment is the whole grant: no assignment, no token, no tool.
Called by agents/setup_agents.py after the agents exist; can also be run alone:

    python -m identity.assign_agent_roles --principal <agentIdentityObjectId> --role Support.Tools

Needs, in delegated mode: ownership of the gateway service principal plus the
right to assign app roles to service principals. If your tenant restricts that,
an admin with the Cloud Application Administrator role runs this command.
"""

from __future__ import annotations

import argparse

from identity import graph
from identity.azd_env import get_values, require
from identity.setup_gateway_app import role_id


def existing_assignments(resource_sp_id: str, principal_id: str) -> set[str]:
    found = graph.request("GET", f"/servicePrincipals/{principal_id}/appRoleAssignments?$select=appRoleId,resourceId")
    return {a["appRoleId"] for a in found.get("value", []) if a["resourceId"] == resource_sp_id}


def assign(resource_sp_id: str, principal_id: str, role_value: str) -> bool:
    """Returns True when a new assignment was created."""
    wanted = role_id(role_value)
    if wanted in existing_assignments(resource_sp_id, principal_id):
        return False
    graph.request(
        "POST",
        f"/servicePrincipals/{resource_sp_id}/appRoleAssignedTo",
        {"principalId": principal_id, "resourceId": resource_sp_id, "appRoleId": wanted},
        retries=8,
    )
    return True


def revoke(resource_sp_id: str, principal_id: str, role_value: str) -> bool:
    wanted = role_id(role_value)
    found = graph.request("GET", f"/servicePrincipals/{resource_sp_id}/appRoleAssignedTo?$filter=principalId eq {principal_id}")
    removed = False
    for a in found.get("value", []):
        if a["appRoleId"] == wanted:
            graph.request("DELETE", f"/servicePrincipals/{resource_sp_id}/appRoleAssignedTo/{a['id']}")
            removed = True
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--principal", required=True, help="Object (principal) ID of the agent identity")
    parser.add_argument("--role", required=True, choices=["Support.Tools", "Docs.Tools", "CustOps.Tools"])
    parser.add_argument("--revoke", action="store_true", help="Remove the assignment instead")
    args = parser.parse_args()
    (sp_id,) = require(get_values(), "MCP_GATEWAY_SP_ID")
    if args.revoke:
        print("Removed." if revoke(sp_id, args.principal, args.role) else "No such assignment.")
    else:
        print("Assigned." if assign(sp_id, args.principal, args.role) else "Already assigned.")


if __name__ == "__main__":
    main()
