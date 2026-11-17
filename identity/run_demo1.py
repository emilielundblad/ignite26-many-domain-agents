"""Demo 1: per-domain identities in Entra. Read-only; changes nothing.

Walks the five steps on the Demo 1 slide, in order, pausing between steps so you
can switch to the Entra admin center and record the matching portal view:

  1. The agent identities Foundry created: each agent with its own blueprint
  2. The Support agent: blueprint, sponsors, recent sign-ins
  3. The gateway app: assignment required, and who holds which role
  4. Conditional Access: only approved agents reach the gateway (report-only)
  5. Lifecycle: the default inactivity policy, free but off until you enable it

    python -m identity.run_demo1              # pauses between steps, masks IDs for recording
    python -m identity.run_demo1 --no-pause   # straight through
    python -m identity.run_demo1 --show-ids   # full object IDs (do not record this)

Permissions: reading service principals works for any member. Sponsors, sign-in
logs and Conditional Access need a reader role (for example Security Reader or
Global Reader, activated just in time). Anything you cannot read is reported with
the portal path to show instead; the demo carries on.

Portal steps and the one-time preparation are in docs/demo-1-runbook.md.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from identity import graph
from identity.azd_env import get_values, require
from identity.setup_gateway_app import APP_ROLES, role_id

STATE = Path(__file__).resolve().parent.parent / ".ig26" / "agents.json"
GUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
REPORT_ONLY = "enabledForReportingButNotEnforced"


class Out:
    def __init__(self, show_ids: bool, pause: bool):
        self.show_ids = show_ids
        self.pause = pause

    def id(self, value: str | None) -> str:
        if not value:
            return "n/a"
        return value if self.show_ids else mask(value)

    def step(self, n: int, title: str, portal: str) -> None:
        if self.pause and n > 1:
            input("\n[Enter] for the next step ")
        print(f"\n{'=' * 72}\nSTEP {n}  {title}\n{'=' * 72}")
        print(f"Portal: {portal}\n")


def mask(value: str) -> str:
    """Keep the first 4 characters of each GUID so viewers can match objects, hide the rest."""
    return GUID.sub(lambda m: m.group(0)[:4] + "****-****", value)


def try_get(path: str):
    try:
        return graph.request("GET", path, retries=2), None
    except graph.GraphError as exc:
        return None, f"not readable with your current role ({exc.status} {exc.code})"


def step1(out: Out, agents: list[dict]) -> None:
    # Each agent has its own blueprint and default instance identity from creation:
    # https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity
    out.step(1, "Agent identities: each agent has its own blueprint",
             "Entra admin center > Agent ID > Agent identities (open an agent to see its blueprint)")
    for a in agents:
        sp, err = try_get(f"/servicePrincipals/{a['instanceIdentity']['principalId']}?$select=displayName,appId,servicePrincipalType")
        bp = (a.get("blueprint") or {}).get("clientId")
        print(f"  project {a['project']:<8} blueprint {out.id(bp):<22} agent identity {a['name']}")
        if sp:
            print(f"      display name {sp.get('displayName')}, type {sp.get('servicePrincipalType', 'n/a')}, client id {out.id(sp.get('appId'))}")
        elif err:
            print(f"      {err}")
    print("  project custops  no agent: the domain exists but is not enabled")
    print("\n  Say: every agent gets its own blueprint and its own identity at creation. No secrets anywhere.")


def step2(out: Out, agents: list[dict]) -> None:
    out.step(2, "The Support agent: blueprint, sponsors, sign-ins",
             "Agent ID > Agent identities > the Support agent > Overview, Sponsors, Sign-in logs")
    a = next((x for x in agents if x["name"] == "support-agent"), None)
    if not a:
        print("  support-agent not found in .ig26/agents.json")
        return
    pid = a["instanceIdentity"]["principalId"]
    cid = a["instanceIdentity"]["clientId"]
    print(f"  agent identity  {out.id(pid)}   blueprint {out.id((a.get('blueprint') or {}).get('clientId'))}")
    sponsors, err = try_get(f"/servicePrincipals/{pid}/microsoft.graph.agentIdentity/sponsors?$select=id,displayName")
    if sponsors is not None:
        names = [s.get("displayName") or out.id(s["id"]) for s in sponsors.get("value", [])]
        print(f"  sponsors        {', '.join(names) if names else 'NONE: add one in the portal before recording (runbook, prepare step 2)'}")
    else:
        print(f"  sponsors        {err}; show them in the portal")
    signins, err = try_get(
        "/auditLogs/signIns?$top=5&$orderby=createdDateTime desc"
        f"&$filter=signInEventTypes/any(t:t eq 'servicePrincipal') and appId eq '{cid}'"
    )
    if signins is not None:
        rows = signins.get("value", [])
        if not rows:
            print("  sign-ins        none yet: run python -m agents.run_demo2 first, sign-in logs arrive within minutes")
        for r in rows:
            print(f"  sign-in         {r.get('createdDateTime')}  resource {r.get('resourceDisplayName')}  result {(r.get('status') or {}).get('errorCode')}")
    else:
        print(f"  sign-ins        {err}; show Sign-in logs > Service principal sign-ins in the portal")


def step3(out: Out, sp_id: str) -> None:
    out.step(3, "The gateway app: assignment required, and who holds which role",
             "Enterprise applications > ig26-mcp-gateway-<env> > Properties, then Users and groups")
    sp, err = try_get(f"/servicePrincipals/{sp_id}?$select=displayName,appId,appRoleAssignmentRequired")
    if not sp:
        print(f"  {err}")
        return
    print(f"  {sp['displayName']}   audience api://{out.id(sp['appId'])}")
    print(f"  assignment required: {'YES' if sp.get('appRoleAssignmentRequired') else 'NO  <-- fix before recording'}")
    found, err = try_get(f"/servicePrincipals/{sp_id}/appRoleAssignedTo?$select=appRoleId,principalDisplayName,principalId")
    holders: dict[str, list[str]] = {v: [] for v, _, _ in APP_ROLES}
    by_id = {role_id(v): v for v, _, _ in APP_ROLES}
    for x in (found or {}).get("value", []):
        role = by_id.get(x["appRoleId"])
        if role:
            holders[role].append(x.get("principalDisplayName") or out.id(x["principalId"]))
    for role, who in holders.items():
        print(f"  {role:<15} {', '.join(who) if who else 'nobody'}")
    print("\n  Say: no role, no token, no tool. Nobody holds CustOps.Tools, so that domain is unreachable.")


def step4(out: Out, agents: list[dict]) -> None:
    # "Allow only approved agents": custom security attributes on each agent identity,
    # targeted by a Conditional Access policy in report-only.
    # https://learn.microsoft.com/entra/identity/conditional-access/policy-autonomous-agents
    out.step(4, "Conditional Access: only approved agents reach the gateway",
             "Conditional Access > Policies > ig26-block-unapproved-agents (and Policy plans, preview)")
    for a in agents:
        sp, err = try_get(f"/servicePrincipals/{a['instanceIdentity']['principalId']}?$select=displayName,customSecurityAttributes")
        if sp is None:
            print(f"  {a['name']:<14} attributes {err}; show them on the agent identity page")
            continue
        attrs = ((sp.get("customSecurityAttributes") or {}).get("AgentAttributes") or {})
        status = attrs.get("AgentApprovalStatus") or []
        status = status if isinstance(status, list) else [status]
        flag = ", ".join(status) if status else "NOT SET  <-- run python -m identity.tag_agents before recording"
        print(f"  {a['name']:<14} AgentAttributes.AgentApprovalStatus = {flag}")
    found, err = try_get("/identity/conditionalAccess/policies?$select=id,displayName,state")
    if found is None:
        print(f"  policies {err}; show them in the portal")
        return
    ours = [p for p in found.get("value", []) if p.get("displayName", "").lower().startswith("ig26")]
    if not any(p.get("displayName") == "ig26-block-unapproved-agents" for p in ours):
        print("  Policy ig26-block-unapproved-agents not found. Create it before recording (runbook, prepare step 3).")
    for p in ours:
        flag = "report-only" if p.get("state") == REPORT_ONLY else f"{p.get('state')}  <-- expected report-only"
        print(f"  {p['displayName']:<40} {flag}")
    print("\n  Say: agents without AgentApprovalStatus = Gateway_Approved are blocked at the gateway app.")
    print("  The attribute is set per agent identity; approval is explicit, reviewable and revocable.")
    print("  Policy plans are preview; show the plan and its two rules in the portal.")


def step5(out: Out) -> None:
    # Free in every tenant, but off until someone enables it:
    # https://learn.microsoft.com/entra/id-governance/agent-default-inactivity-policy
    out.step(5, "Lifecycle: the default inactivity policy",
             "Identity governance > Lifecycle Workflows > Lifecycle Policies > Agent ID (preview)")
    print("  The default inactivity policy ships in every tenant at no cost, but it is OFF until you enable it.")
    print("  Once enabled it notifies owners and sponsors of inactive agents, then disables and deletes them.")
    print("  Show the Enable policy toggle (prepare step 4 switched it on), then the reconfirmation policy you added.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo 1, read-only walkthrough")
    parser.add_argument("--no-pause", action="store_true")
    parser.add_argument("--show-ids", action="store_true", help="print full object IDs (do not record)")
    args = parser.parse_args()

    (sp_id,) = require(get_values(), "MCP_GATEWAY_SP_ID")
    if not STATE.exists():
        raise SystemExit("No agents yet. Run `azd up` first; it creates the agents and .ig26/agents.json.")
    agents = json.loads(STATE.read_text())["agents"]
    out = Out(show_ids=args.show_ids, pause=not args.no_pause)

    print("Demo 1: per-domain identities in Entra (read-only)")
    step1(out, agents)
    step2(out, agents)
    step3(out, sp_id)
    step4(out, agents)
    step5(out)
    print("\nDone. Nothing was changed.")


if __name__ == "__main__":
    main()
