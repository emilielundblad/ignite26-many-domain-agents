# Validation

## Checked on every pull request (`.github/workflows/ci.yml`)

| Check | Tool |
|---|---|
| Bicep compiles and passes the linter (secrets in parameters and outputs are errors) | `az bicep build`, `az bicep lint` |
| API Management policies are well formed, every placeholder is replaced, every named value exists, no `&&`, no response body reads | `tests/check_policies.py` |
| Mock APIs: behaviour, validation, security headers, OpenAPI document matches routes | `pytest` (23 tests) |
| Setup scripts: Entra app shape, idempotent role assignment, agent definitions, boundary configuration | `pytest tests` (16 tests, no Azure calls) |
| Lint and security lint for Python | `ruff` with bandit rules |
| Images build | `docker build` |
| Code scanning, dependency review | CodeQL, dependency-review-action |

## Only a live run proves

These depend on service behaviour that cannot be tested offline. Run `azd up`, then demos 2 and 3, after any change to them:

- API Management accepts the MCP server definition (`mcpTools`) and the policies (the October 2026 release validates policies more strictly).
- Foundry accepts the `AgenticIdentityToken` and `ProjectManagedIdentity` connections and the model route `ig26-models/<deployment>`.
- Agent identity tokens carry the gateway app roles, and the MCP server forwards `x-ig26-agent-token` to the REST API scope.
- Content safety blocks the jailbreak sample; the Support token budget returns 429.

If one of these fails, [troubleshooting.md](troubleshooting.md) has the fallback for each, and please open an issue with the error text (no tenant IDs).
