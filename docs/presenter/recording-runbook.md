# Step 6: Recording runbook (you)

## General

- 1920 x 1080, browser zoom 125 percent, code and XML at 150 percent. Dark or light theme consistently across all four clips.
- Notifications off, bookmarks bar hidden, a clean browser profile signed in only to the lab tenant. No real email addresses or tenant names on screen.
- Pre-open every tab before recording. Never navigate from a home page.
- Two takes per demo. Edit each clip to the length in the table; speed up waits rather than cutting mid-action so it stays honest.
- Narrate live on stage over the clip; record the clips without voice, or with a scratch voice track you can mute.
- Add a small "Recorded" label in a corner of each clip.

| Demo | Target length | Clip file |
|---|---|---|
| 1 | 2:00 | `clip1-identities.mp4` |
| 2 | 2:45 | `clip2-trace-boundary.mp4` |
| 3 | 2:15 | `clip3-gateway-fleet.mp4` |
| 4 | 2:15 | `clip4-ai-universe.mp4` |

## Demo 1: Per-domain identities (native build)

1. 10 s: Claude Code session showing the step 3 prompt and the approved plan (blur any IDs).
2. Terminal: `python -m identity.run_demo1` (IDs are masked). Full shot list and preparation: [demo-1-runbook.md](../demo-1-runbook.md).
3. Entra admin center > Agent ID > Agent identities, filtered by blueprint: one per domain project.
4. Open the Support agent identity: blueprint, sponsor, sign-in logs.
5. Enterprise applications > `ig26-mcp-gateway-<env>`: assignment required, and the app role assignments (Support holds Support.Tools and Docs.Tools; nobody holds CustOps.Tools).
6. Conditional Access in report-only: the policy plan `ig26-agents-at-risk` and the policy targeting the `custops` blueprint (say: it targets the blueprint, so future agents are covered).

## Demo 2: Trace one request, then break a boundary (native build)

1. Run `python -m agents.run_demo2`, request (a). Show the answer with citations.
2. Foundry > Tracing > the trace: agent invocation, MCP tool call via APIM, model call, response.
3. Run request (b), the credit note.
4. Open that trace: the denied tool call, 403 from APIM, identity and reason. Optional 5 s: credit-note API logs show zero calls.

## Demo 3: Gateway policy and the fleet (native build)

1. APIM > MCP server `mcp-support-tickets` > policy: `validate-azure-ad-token`, `llm-content-safety`.
2. The content safety test result in the trace.
3. Token metrics by domain (`python -m agents.run_demo3` output or the KQL it prints). Skip if behind on stage.
4. Foundry Control Plane: fleet inventory and risk dimensions.
5. Compliance pane: Purview data security toggle and data risk signals.

## Demo 4 (session only): From Marketplace to a governed app (Fortytwo AI Universe lab)

Not reproducible from this repo. Disclosure: the author is a board member of Fortytwo.

Agree the recording window and a change freeze with the lab owners first.

1. 10 s: Microsoft Marketplace listing for Fortytwo AI Universe.
2. 5 s: the completed install (say "about an hour, most of it API Management").
3. Create an app: show the data classification, personal data and EU AI Act risk questions.
4. The new app's resource group in the Azure portal: Container App, Key Vault, PostgreSQL with private endpoints, managed identity. Then its GitHub repo and Foundry project and agent.
5. Open the repo in Claude Code: show the Wisdom MCP connected and one organisation rule being applied.
6. Commit a change containing a documented example credential string (for example the sample AWS access key from AWS documentation, never a real key) and show CI blocking the publish.
7. Compliance area: AI system register entry and the evidence pack download.

If step 5 or 6 is fragile in the lab, record them separately and cut them in; they are the coding-agent payoff of the talk.
