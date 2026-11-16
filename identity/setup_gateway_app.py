"""Create (or reuse) the Entra application that represents the governed MCP gateway.

Runs automatically as the azd `preprovision` hook. Idempotent.

What it creates, in your tenant, with your own delegated rights:
- App registration `ig26-mcp-gateway-<env>`: single tenant, identifier URI
  api://<appId>, v2 access tokens, three application-only app roles
  (Support.Tools, Docs.Tools, CustOps.Tools). No credentials: nothing ever signs
  in as this app; it only receives tokens.
- Its service principal, with "assignment required" on, so only principals that
  hold one of the app roles can get a token for it.

Why: agents get tokens for this audience, API Management validates them, and the
app role in the token decides which domain's tools the agent may call. The
assignment is an Entra object you can review, expire or revoke, and Conditional
Access can target the gateway because it has a service principal.

Needs: permission to register applications in the tenant (the default for members
unless an admin turned it off) or the Application Developer role.
"""

from __future__ import annotations

import uuid

from identity import graph
from identity.azd_env import get_values, require, set_value

ROLE_NAMESPACE = uuid.UUID("6f1c3c63-0e4e-4f3f-9a54-6b7d1f2a2a26")
APP_ROLES = [
    ("Support.Tools", "Support domain tools", "Call the Support domain MCP tools (tickets)."),
    ("Docs.Tools", "Documentation domain tools", "Call the Documentation domain MCP tools (product knowledge)."),
    ("CustOps.Tools", "Customer operations tools", "Call the Customer operations MCP tools (credit notes). Not granted to any agent in this lab."),
]


def role_id(value: str) -> str:
    return str(uuid.uuid5(ROLE_NAMESPACE, value))


def desired_roles() -> list[dict]:
    return [
        {
            "id": role_id(value),
            "value": value,
            "displayName": name,
            "description": desc,
            "allowedMemberTypes": ["Application"],
            "isEnabled": True,
        }
        for value, name, desc in APP_ROLES
    ]


def ensure_app(display_name: str) -> dict:
    found = graph.request("GET", f"/applications?$filter=displayName eq '{display_name}'&$select=id,appId,displayName,appRoles,identifierUris,api")
    apps = found.get("value", [])
    if len(apps) > 1:
        raise SystemExit(f"More than one application is named {display_name}. Delete the extras or set MCP_GATEWAY_APP_ID yourself.")
    if apps:
        app = apps[0]
        print(f"Reusing app registration {display_name} ({app['appId']})")
    else:
        app = graph.request(
            "POST",
            "/applications",
            {
                "displayName": display_name,
                "signInAudience": "AzureADMyOrg",
                "notes": "Ignite 2026 lab: audience for agent tokens to the governed MCP gateway in API Management. No credentials by design.",
                "tags": ["ig26", "event:ignite2026"],
                "api": {"requestedAccessTokenVersion": 2},
                "appRoles": desired_roles(),
            },
        )
        print(f"Created app registration {display_name} ({app['appId']})")

    patch = {}
    uri = f"api://{app['appId']}"
    if uri not in (app.get("identifierUris") or []):
        patch["identifierUris"] = [uri]
    existing = {r["value"]: r for r in app.get("appRoles") or []}
    if any(v not in existing for v, _, _ in APP_ROLES):
        merged = list(existing.values()) + [r for r in desired_roles() if r["value"] not in existing]
        patch["appRoles"] = merged
    if (app.get("api") or {}).get("requestedAccessTokenVersion") != 2:
        patch["api"] = {"requestedAccessTokenVersion": 2}
    if patch:
        graph.request("PATCH", f"/applications/{app['id']}", patch)
    return graph.request("GET", f"/applications/{app['id']}?$select=id,appId,displayName,appRoles,identifierUris")


def ensure_service_principal(app_id: str) -> dict:
    found = graph.request("GET", f"/servicePrincipals?$filter=appId eq '{app_id}'&$select=id,appId,appRoleAssignmentRequired")
    if found.get("value"):
        sp = found["value"][0]
    else:
        sp = graph.request("POST", "/servicePrincipals", {"appId": app_id, "tags": ["HideApp", "ig26"]})
        print(f"Created service principal {sp['id']}")
    if not sp.get("appRoleAssignmentRequired"):
        graph.request("PATCH", f"/servicePrincipals/{sp['id']}", {"appRoleAssignmentRequired": True})
    return sp


def main() -> None:
    values = get_values()
    (env_name,) = require(values, "AZURE_ENV_NAME")
    app = ensure_app(f"ig26-mcp-gateway-{env_name}")
    sp = ensure_service_principal(app["appId"])
    set_value("MCP_GATEWAY_APP_ID", app["appId"])
    set_value("MCP_GATEWAY_SP_ID", sp["id"])
    print(f"MCP gateway app ready. Audience: api://{app['appId']}. App roles: {', '.join(v for v, _, _ in APP_ROLES)}.")


if __name__ == "__main__":
    try:
        main()
    except graph.GraphError as exc:
        hint = ""
        if exc.status in (401, 403):
            hint = (
                "\nYour account could not register an application. Ask an admin for the Application Developer role, "
                "or ask them to create the app as described in identity/README.md and run "
                "`azd env set MCP_GATEWAY_APP_ID <appId>` and `azd env set MCP_GATEWAY_SP_ID <servicePrincipalObjectId>`."
            )
        raise SystemExit(f"{exc}{hint}") from None
