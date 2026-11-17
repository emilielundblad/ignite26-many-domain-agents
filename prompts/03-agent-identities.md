# Step 3: Per-domain agent identities (Claude Code). Source of Demo 1

> **Note:** the code these prompts produce is already in this repository. Use the prompt to rebuild a step from scratch, to extend it, or to show on stage how it was built.

---

Read CLAUDE.md first and follow it. This step changes Entra, so every write needs my explicit approval in the chat.

Goal: an agent identity blueprint and agent identity per agent (the Foundry default), a human sponsor on each, Conditional Access that allows only approved agents, and access packages that govern what each agent can request. This is the Demo 1 environment.

Before writing anything, read these Learn pages and summarise for me what is GA and what is preview today:
- Agent identity blueprints; Create a blueprint; Manage blueprints
- Agent ID known issues and FAQ
- Conditional Access for agent identities; Target agent identities in CA policies
- Access packages for agent identities; Agent identity sponsor tasks in Lifecycle Workflows

Then, with a checkpoint before each write:

1. Graph permissions: list the minimum application or delegated permissions and Entra roles you need (for example `AgentIdentityBlueprint.Create`, Agent ID Developer or Agent ID Administrator). I will activate my own role through PIM and run the creation from my session; you write the script (`identity/create-blueprints.ps1` using Microsoft Graph PowerShell or `az rest`).
2. Blueprints `bp-ig26-support`, `bp-ig26-docs`, `bp-ig26-custops`, single-tenant, sponsor = <sponsor user or Microsoft 365 group>. Production-style credential: a federated credential backed by a user-assigned managed identity, as Learn recommends; no client secrets.
3. Grant `AgentIdentity.CreateAsManager` explicitly to each blueprint principal where needed. Since 4 November 2026 it is no longer granted automatically (MC1506728).
4. Agent identities: `agent-ig26-support`, `agent-ig26-docs` from their blueprints. Create none for Customer ops yet; the domain exists but is not enabled.
5. Custom security attribute set `AgentDomain` with attribute `domain` (support, docs, custops), assigned to the agent identities.
6. Conditional Access in REPORT-ONLY, built as a policy plan (preview since 4 Nov 2026; read "Conditional Access policy plans" on Learn first): plan `ig26-agents-at-risk` with the shared condition agent risk = high and a shared exclusion for break-glass identities, rule 1 for agent users and rule 2 for agent identities, both Block. Plus one policy targeting all agents from `bp-ig26-custops` with Block. Check the licensing note on Learn for agent risk. I switch them on.
6b. Tenant hygiene after the 4 Nov changes: show me the current value of "Users can create agent blueprints" and propose setting it to No; confirm user consent to third-party apps is restricted (BluePhishing). Do not change either without my approval.
6c. Agent ID lifecycle policies (preview): show me the default inactivity policy and propose a reconfirmation policy for the demo blueprints.
7. Access packages in Entra ID Governance: `ap-support-knowledge-read` (Support agent may request read on the knowledge API app role or group, time-bound 30 days, sponsor approves). Confirm on Learn which resource types agents can request; app roles may not be supported, in which case use a security group mapped in API Management.
8. Write `docs/demo-1-runbook.md`: the exact portal views to open, in order, for recording.

Acceptance: in the Entra admin center, Agent identities filtered by blueprint shows Support and Documentation with their sponsor; the CA policies show in report-only; the access package exists and a request from the Support agent identity reaches the sponsor for approval.

What I will record (Demo 1): the prompt for step 2 on screen for 10 seconds, then the portal walk in `docs/demo-1-runbook.md`.
