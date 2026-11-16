# Demo 1 runbook: per-domain identities in Entra

Demo 1 is mostly a portal walk, because the interesting objects (blueprints, identities, sponsors, Conditional Access, lifecycle) live in Entra. The script `identity/run_demo1.py` drives the order, prints the facts you point at, and checks that everything is in place before you record. It changes nothing.

## What the slide promises, and where it comes from

| Slide step | Created by | Shown with |
|---|---|---|
| 1. Agent identities, one blueprint per domain project | Foundry, when `azd up` creates the agents | `run_demo1` step 1, then Agent ID > Agent identities |
| 2. Support agent: blueprint, sponsor, sign-ins | Foundry (identity), **you** (sponsor, prepare step 2) | `run_demo1` step 2, then the agent identity page |
| 3. Gateway app: assignment required, who holds which role | `azd up` (preprovision and postdeploy hooks) | `run_demo1` step 3, then Enterprise applications |
| 4. Policy plan for agents at risk, rule on the Customer ops blueprint, report-only | **You** (prepare step 3) | `run_demo1` step 4, then Conditional Access |
| 5. Lifecycle: default inactivity policy | Exists by default; **you** add a reconfirmation policy (prepare step 4) | Identity governance > Agent ID lifecycle policies |

Why some steps are manual: sponsors can only be written through Graph with an application permission, and the Graph shape for targeting agents in Conditional Access is not documented in v1.0 yet. Rather than give a script tenant-wide power or guess an API, these are portal steps you do once, with your own just-in-time admin role.

## Prepare (once, 30 minutes, before recording)

Activate the roles you need in Privileged Identity Management for this session only: Agent ID Administrator (sponsors), Conditional Access Administrator (policies), Lifecycle Workflows Administrator or Identity Governance Administrator (lifecycle).

1. **Deploy and warm up.** `azd up`, then `python -m agents.run_demo2` once, so the Support agent has sign-in logs.
2. **Add a sponsor** to the Support agent and the Documentation agent: Entra admin center > Agent ID > Agent identities > the agent > Sponsors > Add sponsors > a lab user (or a Microsoft 365 group). Repeat on the blueprint if your tenant shows sponsors there.
3. **Conditional Access, report-only.** Conditional Access > Policies:
   - Policy plan (preview): Conditional Access > Policy plans > New plan `ig26-agents-at-risk`. Shared condition: agent risk = High. Shared exclusion: your break-glass accounts. Rule 1: agent users, grant Block. Rule 2: agent identities, grant Block. State **Report-only**.
   - Policy `ig26-block-custops-agents`: Assignments > Agents (preview) > select agent identities by blueprint > the `custops` project's blueprint. Target resources: the app `ig26-mcp-gateway-<env>`. Grant: Block. State **Report-only**.
   - The `custops` project has no agent yet, so Foundry may not have created its blueprint. If it is not listed, create a draft agent in that project in the Foundry portal (no tools, do not publish), which creates the blueprint, and do not grant it any gateway role.
   - Agent risk needs Entra ID P2 while in preview; Conditional Access for agents needs P1 and, per Learn, Agent 365 licensing. If your lab tenant lacks them, record the policy screens in another lab tenant or show the Learn page instead.
4. **Lifecycle (preview).** Identity governance > Agent ID lifecycle policies: open the default inactivity policy (do not change it), and add a reconfirmation policy scoped to the lab blueprints, owner = your lab user.
5. **Check.** `python -m identity.run_demo1 --no-pause`. Every step should print without "fix before recording" or "expected report-only".

## Record (target 1:45)

Screen: 1920 x 1080, browser at 125 percent, terminal font 18 pt, a browser profile signed in only to the lab tenant. IDs are masked by the script; blur any IDs that the portal shows.

| Time | Terminal | Portal |
|---|---|---|
| 0:00 | `python -m identity.run_demo1`, step 1 | Agent ID > Agent identities, filter by blueprint: one per domain project |
| 0:20 | step 2 | The Support agent: Overview (blueprint), Sponsors, Sign-in logs |
| 0:45 | step 3 | Enterprise applications > `ig26-mcp-gateway-<env>`: Properties (assignment required: Yes), then the role assignments |
| 1:10 | step 4 | Conditional Access: policy plan `ig26-agents-at-risk` and its two rules, then `ig26-block-custops-agents`, both report-only |
| 1:35 | step 5 | Agent ID lifecycle policies: the default inactivity policy |

Land the point on step 4: the rule targets the blueprint, so the next Customer ops agent is covered before it exists. Access is an Entra object you can review and revoke; no code change grants a tool.

## Tear down

The Conditional Access policies, the policy plan, sponsors and the lifecycle policy are not removed by `scripts/teardown.py`, because you created them by hand. Delete them in the portal after the session.
