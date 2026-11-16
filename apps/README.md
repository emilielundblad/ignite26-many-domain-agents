# apps

Three mock line-of-business APIs with fake data, one per domain. Python 3.12, FastAPI, hash-pinned dependencies, non-root containers. Each serves a curated OpenAPI 3.0 document at `/openapi.json`; API Management imports that document and turns its `operationId`s into MCP tools, and a test keeps the document and the routes in sync.

| App | Domain | Operations (MCP tools) |
|---|---|---|
| `ticketing-api` | Support | `list-tickets`, `get-ticket`, `add-ticket-note` |
| `knowledge-api` | Documentation | `search-articles`, `get-article` |
| `creditnote-api` | Customer operations (not enabled) | `create-credit-note`; logs `CREDITNOTE-CALL-RECEIVED` on every call so "zero calls" can be proven |

Ticket 1042 is the product fault for Demo 2. Ticket 1043 contains a planted instruction to show that tool output is data.

Run the tests locally:

```bash
cd apps/ticketing-api
python -m pip install --require-hashes -r requirements.txt -r ../requirements-dev.txt
python -m pytest -q
```

Update dependencies with `pip-compile --generate-hashes requirements.in` (pip-tools).
