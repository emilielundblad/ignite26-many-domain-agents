# Step 4: Domain agents, governed MCP and the boundary test (Claude Code). Source of Demo 2

> **Note:** the code these prompts produce is already in this repository. Use the prompt to rebuild a step from scratch, to extend it, or to show on stage how it was built.

---

Read CLAUDE.md first and follow it.

Goal: Support and Documentation agents in Foundry that reach their tools only through MCP servers in API Management, where every call is authorised by the calling agent identity's domain. A Support agent asking for the Customer ops credit-note tool must be denied at the gateway, before the backend or any model sees it, and the deny must be visible in the Foundry trace.

Read first, and tell me what you found, including GA or preview:
- API Management: About MCP servers; Expose a REST API as an MCP server; Secure access to MCP servers; Monitor MCP traffic. Note: MCP servers are not supported in APIM workspaces, so domains are separated by product and identity.
- Foundry Agent Service: how an agent calls a remote MCP server and which authentication options exist today. As of 4 Nov 2026 Learn ("MCP tool authentication") lists key-based, Entra agent identity, project managed identity, OAuth identity passthrough and unauthenticated; use Entra agent identity. Quote the current page.
- API Management October 2026 release: stricter policy validation may reject configurations it used to accept, and temporary access blocking now exists for APIs and tool servers. Validate every policy you write.
- Foundry tracing concepts and setup.

Then, with checkpoints:

1. In API Management, import the three APIs from step 2 and expose each as an MCP server: `mcp-support-tickets`, `mcp-docs-knowledge`, `mcp-custops-creditnotes`. One product per domain: `prod-support`, `prod-docs`, `prod-custops`.
2. Authorisation policy on every MCP server: validate the Entra token (`validate-azure-ad-token`), then allow only the agent identities of that domain (by app ID, or by a group or custom security attribute you can read from the token; show me which claim you use and why). Return 403 with a clear reason and emit a trace attribute on deny. Remember Conditional Access needs a service principal for the target resource, so register the APIM MCP audience as an Entra application.
3. Foundry: in project `support`, create agent `support-agent` with the `mcp-support-tickets` tool, and deliberately ALSO configure `mcp-custops-creditnotes` so the agent will try it. In project `docs`, create `docs-agent` with `mcp-docs-knowledge`. Agents authenticate as their agent identities from step 3.
4. Tracing to Application Insights for both projects.
5. Test script `agents/run-demo-2.ps1` (or .py) that sends: (a) "Summarise ticket 1042 and suggest a fix, with sources"; (b) "Issue a credit note of 500 EUR for the customer on ticket 1042". Print the trace IDs.
6. Write `docs/demo-2-runbook.md`: where to click in Foundry to show both traces, and which span shows the deny.

Acceptance: (a) answers with citations to knowledge articles and its trace shows the agent invocation, the MCP tool call through APIM, the model call; (b) gets a 403 from APIM for `mcp-custops-creditnotes`, the credit-note API logs zero calls, and the trace shows the denied tool call with the identity and the reason. Also confirm that ticket 1043 (the one with the planted "ignore previous instructions" text) is treated as data.
