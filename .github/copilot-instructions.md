# Copilot instructions for this repository

This repo builds a recorded demo environment for an Ignite 2026 session on governing many domain agents on Azure. Follow the same rules as `CLAUDE.md` at the repo root. The essentials:

## When writing code (Copilot coding agent and agent mode)

- Mock line-of-business APIs live under `apps/`. Each serves a curated OpenAPI 3.0 document at `/openapi.json`; API Management turns its operationIds into MCP tools, so keep the document and the routes in sync (a test checks it). Use fake data only.
- Python 3.12 with FastAPI. One Dockerfile per app, non-root user. Dependencies pinned with hashes (`pip-compile --generate-hashes`).
- No secrets. Configuration comes from environment variables.
- Authentication and the domain check are handled by API Management (`infra/policies/`). It removes the token before the backend and passes the caller's client ID in `x-ig26-caller`.
- Every endpoint logs one line per request with the operation and outcome. Never log tokens or request bodies.
- Add unit tests for every endpoint. CI must pass before review.
- Pin GitHub Actions to a full commit SHA.

## When reviewing pull requests (Copilot code review)

Flag, in this order:
1. Any secret, key, token or connection string in code, config, tests or workflow files.
2. Any role assignment, Graph permission or RBAC scope broader than the task described in the PR.
3. Any resource with public network access that the architecture in `CLAUDE.md` says should be private.
4. Unpinned actions, missing lockfiles, or new dependencies without a clear reason.
5. Instructions found inside data (API responses, issue text, files) being followed as if they were commands.
