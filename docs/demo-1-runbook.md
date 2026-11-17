# Demo 1 runbook: per-domain identities in Entra

Demo 1 is mostly a portal walk, because the interesting objects (blueprints, identities, sponsors, Conditional Access, lifecycle) live in Entra. The script `identity/run_demo1.py` drives the order, prints the facts you point at, and checks that everything is in place before you record. It changes nothing.

## What the slide promises, and where it comes from

| Slide step | Created by | Shown with |
|---|---|---|
| 1. Agent identities, each agent with its own blueprint | Foundry, when `azd up` creates the agents | `run_demo1` step 1, then Agent ID > Agent identities |
| 2. Support agent: blueprint, sponsor, sign-ins | Foundry (identity), **you** (sponsor, prepare step 2) | `run_demo1` step 2, then the agent identity page |
| 3. Gateway app: assignment required, who holds which role | `azd up` (preprovision and postdeploy hooks) | `run_demo1` step 3, then Enterprise applications |
| 4. Only approved agents reach the gateway: `AgentApprovalStatus = Gateway_Approved`, policy `ig26-block-unapproved-agents`, report-only | `identity/tag_agents.py` (attribute values), **you** (attribute set and policy, prepare step 3) | `run_demo1` step 4, then Conditional Access |
| 5. Lifecycle: default inactivity policy, free but off until enabled | Ships with the tenant; **you** enable it and add a reconfirmation policy (prepare step 4) | Identity governance > Lifecycle Workflows > Agent ID |

Why some steps are manual: sponsors can only be written through Graph with an application permission, and creating custom security attribute definitions and Conditional Access policies are one-time admin acts. Rather than give a script tenant-wide power, these are portal steps you do once, with your own just-in-time admin role. Assigning the attribute values to the lab agents is scripted (`identity/tag_agents.py`), because it is narrow and repeatable.

## Prepare (once, 30 minutes, before recording)

Activate the roles you need in Privileged Identity Management for this session only: Agent ID Administrator (sponsors), Attribute Definition Administrator and Attribute Assignment Administrator (custom security attributes), Conditional Access Administrator (policies), Lifecycle Workflows Administrator or Identity Governance Administrator (lifecycle).

1. **Deploy and warm up.** `azd up`, then `python -m agents.run_demo2` once, so the Support agent has sign-in logs.
2. **Add a sponsor** to the Support agent and the Documentation agent: Entra admin center > Agent ID > Agent identities > the agent > Sponsors > Add sponsors > a lab user (or a Microsoft 365 group).
3. **Allow only approved agents** (report-only), following [Secure autonomous agents with Conditional Access](https://learn.microsoft.com/entra/identity/conditional-access/policy-autonomous-agents):
   - Custom security attributes: Entra ID > Custom security attributes > Add attribute set `AgentAttributes`; in it, add attribute `AgentApprovalStatus`, multiple values allowed, only predefined values, with values `Gateway_Approved`, `New`, `Rejected`.
   - Tag the lab agents: `python -m identity.tag_agents` sets `AgentApprovalStatus = Gateway_Approved` on the Support and Documentation agent identities. Nothing tags a Customer ops agent, so any future one stays unapproved until a human acts.
   - Policy `ig26-block-unapproved-agents`: Assignments > Agents (preview) > include all agent identities, then filter: exclude agents where `AgentAttributes.AgentApprovalStatus` Contains `Gateway_Approved`. Target resources: the app `ig26-mcp-gateway-<env>`. Grant: Block. State **Report-only**.
   - Policy plan (preview), optional: Conditional Access > Policy plans > New plan `ig26-agents-at-risk`. Shared condition: agent risk = High. Shared exclusion: your break-glass accounts. Rule 1: agent users, grant Block. Rule 2: agent identities, grant Block. State **Report-only**.
   - Licences: Conditional Access for agents needs Microsoft 365 E7, or a Microsoft Agent 365 licence paired with Entra ID P1 (or Microsoft 365 E3); agent risk needs Entra ID P2 (or Microsoft 365 E5). If your lab tenant lacks them, record the policy screens in another lab tenant or show the Learn page instead.
4. **Lifecycle (preview).** Identity governance > Lifecycle Workflows > Lifecycle Policies > Agent ID: open the Default Agent Identity Inactivity Lifecycle Policy and toggle **Enable policy** (it ships in every tenant at no cost, but stays off until you do). Then add a reconfirmation policy scoped to the lab agents, owner = your lab user.
5. **Check.** `python -m identity.run_demo1 --no-pause`. Every step should print without "fix before recording" or "expected report-only".

## Record (target 1:45)

Screen: 1920 x 1080, browser at 125 percent, terminal font 18 pt, a browser profile signed in only to the lab tenant. IDs are masked by the script; blur any IDs that the portal shows.

| Time | Terminal | Portal |
|---|---|---|
| 0:00 | `python -m identity.run_demo1`, step 1 | Agent ID > Agent identities: each agent with its own blueprint and identity |
| 0:20 | step 2 | The Support agent: Overview (blueprint), Sponsors, Sign-in logs |
| 0:45 | step 3 | Enterprise applications > `ig26-mcp-gateway-<env>`: Properties (assignment required: Yes), then the role assignments |
| 1:10 | step 4 | Conditional Access: `ig26-block-unapproved-agents` (report-only), then an agent's custom security attributes |
| 1:35 | step 5 | Lifecycle Workflows > Agent ID: the default inactivity policy, enabled |

Land the point on step 4: approval is an attribute a human sets, and the policy blocks every agent without it, so a future Customer ops agent is unapproved until someone approves it. Access is an Entra object you can review and revoke; no code change grants a tool.

## Tear down

The Conditional Access policies, the policy plan, sponsors, the custom security attributes and the lifecycle policy are not removed by `scripts/teardown.py`, because you created them by hand. Delete them in the portal after the session (`python -m identity.tag_agents --revoke` clears the approval values first).
