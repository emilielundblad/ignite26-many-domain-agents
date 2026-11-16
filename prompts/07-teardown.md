# Step 7: Teardown after Ignite (Claude Code plans, you execute)

> **Note:** the code these prompts produce is already in this repository. Use the prompt to rebuild a step from scratch, to extend it, or to show on stage how it was built.

`.claude/settings.json` denies delete commands on purpose. Claude Code writes the plan and the script; you run it.

---

Read CLAUDE.md and docs/demo-state.md.

Goal: remove everything this repo created, in a safe order, and leave nothing billing or privileged behind.

1. List every resource tagged `event=ignite2026`, every role assignment created for the deploy identity and the agents, every Entra object we created (blueprints, agent identities, custom security attribute values, Conditional Access policies, access packages, app registrations for MCP audiences) and the GitHub federated credentials.
2. Write `docs/teardown.ps1` that removes them in this order: Conditional Access policies, access packages, agent identities, blueprints, app registrations, role assignments, resource groups, the deploy identity last. Key Vault has purge protection, so note the retention period instead of trying to purge.
3. Show me the plan and the script. Do not run it. I will run it myself after 18 November.
