"""Mark the lab agents as approved for the governed MCP gateway. Idempotent.

Sets the custom security attribute AgentAttributes.AgentApprovalStatus to
Gateway_Approved on each agent identity in .ig26/agents.json. The report-only
Conditional Access policy ig26-block-unapproved-agents targets the gateway app
and blocks every agent that does not carry this value, following the
"allow only specific agents" pattern:
https://learn.microsoft.com/entra/identity/conditional-access/policy-autonomous-agents

The attribute set (AgentAttributes) and the attribute definition
(AgentApprovalStatus, multi-valued, predefined values including Gateway_Approved)
are created once in the portal with the Attribute Definition Administrator role;
see docs/demo-1-runbook.md, prepare step 3. Assigning values here needs the
Attribute Assignment Administrator role on your own signed-in session
(delegated CustomSecAttributeAssignment.ReadWrite.All). Nothing else is changed.

    python -m identity.tag_agents             # approve the lab agents
    python -m identity.tag_agents --revoke    # remove the approval value
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from identity import graph

STATE = Path(__file__).resolve().parent.parent / ".ig26" / "agents.json"
ATTRIBUTE_SET = "AgentAttributes"
ATTRIBUTE = "AgentApprovalStatus"
APPROVED = "Gateway_Approved"


def approval_patch(revoke: bool = False) -> dict:
    """Graph PATCH body assigning (or clearing) the approval attribute value."""
    values: list[str] = [] if revoke else [APPROVED]
    return {
        "customSecurityAttributes": {
            ATTRIBUTE_SET: {
                "@odata.type": "#microsoft.graph.customSecurityAttributeValue",
                f"{ATTRIBUTE}@odata.type": "#Collection(String)",
                ATTRIBUTE: values,
            }
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Approve the lab agents for the gateway")
    parser.add_argument("--revoke", action="store_true", help="remove the approval value")
    args = parser.parse_args()

    if not STATE.exists():
        raise SystemExit("No agents yet. Run `azd up` first; it creates the agents and .ig26/agents.json.")
    agents = json.loads(STATE.read_text())["agents"]

    for a in agents:
        pid = a["instanceIdentity"]["principalId"]
        graph.request("PATCH", f"/servicePrincipals/{pid}", approval_patch(args.revoke))
        state = "removed from" if args.revoke else "set on"
        print(f"{ATTRIBUTE_SET}.{ATTRIBUTE} = {APPROVED} {state} {a['name']}")

    print("Done. The report-only policy ig26-block-unapproved-agents evaluates this value; nothing is enforced.")


if __name__ == "__main__":
    try:
        main()
    except graph.GraphError as exc:
        hint = ""
        if exc.status in (401, 403):
            hint = (
                "\nAssigning custom security attribute values needs the Attribute Assignment Administrator role, "
                "and the attribute set must exist first (docs/demo-1-runbook.md, prepare step 3)."
            )
        raise SystemExit(f"{exc}{hint}") from None
