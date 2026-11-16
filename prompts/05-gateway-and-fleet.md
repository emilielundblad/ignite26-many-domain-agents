# Step 5: Gateway policies and the fleet view (Claude Code). Source of Demo 3

> **Note:** the code these prompts produce is already in this repository. Use the prompt to rebuild a step from scratch, to extend it, or to show on stage how it was built.

---

Read CLAUDE.md first and follow it.

Goal: show policy enforced at the gateway before the model, token budgets and chargeback per domain, and the fleet view in Foundry Control Plane with Purview signals.

Read first and report GA or preview for each: `llm-content-safety`, `llm-token-limit`, `llm-emit-token-metric` policy pages; Foundry Control Plane overview and compliance; Purview for Microsoft Foundry.

Then, with checkpoints:

1. Azure AI Content Safety resource (managed identity auth, no keys) and `llm-content-safety` on the MCP servers and on the model API, with prompt shields on. Use Learn's wording in comments: it checks requests and responses for MCP tools and A2A.
2. Model access through APIM: the Foundry model endpoint as an APIM backend, with `llm-token-limit` per product (`prod-support` and `prod-docs` with different tokens-per-minute so the difference is visible) and `llm-emit-token-metric` with at most five custom dimensions: agent ID, domain, product, model, operation.
3. A test that triggers content safety on an MCP tool argument (a clearly harmful but non-graphic test string from the Content Safety docs) and one that exceeds the Support token limit. Capture both results.
4. Foundry Control Plane: make sure both agents appear in the fleet inventory with their risk dimensions. If agents are not discovered automatically, follow "Register custom agents".
5. Purview: enable the Data security and governance toggle in the Control Plane compliance pane. Explain to me which calls Purview can block (user-context token on chat completions) and which it only audits in our design.
6. An Azure Monitor workbook or KQL query showing token usage by agent and domain for the last 24 hours.
7. Write `docs/demo-3-runbook.md` with the exact views and the policy XML file to show (zoom 150 percent).

Acceptance: the content safety test is blocked at APIM with the reason in the trace; the token limit test returns 429 for Support only; metrics show per-domain usage; Control Plane lists both agents; the Purview toggle is on.
